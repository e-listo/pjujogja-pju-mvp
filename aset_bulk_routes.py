import csv
import io
import hashlib
import zipfile
from flask import Blueprint, request, jsonify, Response, current_app
from openpyxl import Workbook
from sqlalchemy.exc import IntegrityError
from models import db, AsetPJU, KategoriPJU, Wilayah
from auth_routes import role_required
from aset_bulk_service import ASSET, LAMP, BatchError, read_file, validate, persist

# Blueprint belum didaftarkan pada app.py utama.
bp=Blueprint('aset_bulk',__name__)
MAX_FILE=4*1024*1024

def attachment(data,filename,mimetype):
    # Kirim byte langsung; send_file(BytesIO) gagal (fileno) pada pembungkus berkas LiteSpeed.
    return Response(data,mimetype=mimetype,headers={'Content-Disposition':f'attachment; filename="{filename}"','Content-Length':str(len(data)),'Cache-Control':'no-store'})

def prepare():
    f=request.files.get('file')
    if not f or not f.filename:raise BatchError('Pilih berkas')
    raw=f.stream.read(MAX_FILE+1)
    if len(raw)>MAX_FILE:raise BatchError('Maksimum 4 MB sementara')
    try:assets,lamps=read_file(raw,f.filename)
    except BatchError:raise
    except (ValueError,UnicodeError,zipfile.BadZipFile,KeyError) as e:raise BatchError('Berkas tidak sesuai template') from e
    categories={k.kode:k.id for k in KategoriPJU.query.filter_by(aktif=True).all()}
    regions={w.kode_wilayah:w.id_wilayah for w in Wilayah.query.all()}
    codes=[r['kode_aset'].upper() for _,r in assets]
    existing={x[0] for x in db.session.query(AsetPJU.kode_aset).filter(AsetPJU.kode_aset.in_(codes)).all()}
    assets,lamps=validate(assets,lamps,categories,regions,existing)
    return assets,lamps,hashlib.sha256(raw).hexdigest()

@bp.errorhandler(BatchError)
def invalid(e):
    db.session.rollback()
    return jsonify(success=False,error=str(e)),400

@bp.route('/api/aset/import/preview',methods=['POST'])
@role_required('admin','koordinator')
def preview():
    assets,lamps,digest=prepare()
    return jsonify(success=True,valid=True,sha256=digest,total_aset=len(assets),total_lampu=len(lamps),preview_aset=assets[:20],preview_lampu=lamps[:20])

@bp.route('/api/aset/import/commit',methods=['POST'])
@role_required('admin','koordinator')
def commit():
    if request.form.get('confirm')!='yes':raise BatchError('Konfirmasi diperlukan')
    assets,lamps,digest=prepare()
    if request.form.get('sha256')!=digest:raise BatchError('Berkas berbeda dari pratinjau')
    try:return jsonify(success=True,**persist(assets,lamps)),201
    except IntegrityError:return jsonify(success=False,error='Konflik data; seluruh batch dibatalkan'),409
    except Exception:
        current_app.logger.exception('Bulk import gagal')
        return jsonify(success=False,error='Penyimpanan gagal; seluruh batch dibatalkan'),500

@bp.route('/api/aset/import/template',methods=['GET'])
@role_required('admin','koordinator')
def template():
    fmt=request.args.get('format','xlsx')
    if fmt=='csv':
        s=io.StringIO();csv.writer(s).writerow(ASSET)
        return attachment(s.getvalue().encode('utf-8-sig'),'template_aset.csv','text/csv')
    if fmt!='xlsx':raise BatchError('Format tidak didukung')
    w=Workbook();w.active.title='Data_Aset';w.active.append(ASSET);w.create_sheet('Data_Lampu').append(LAMP)
    refs=w.create_sheet('Referensi');refs.append(['kode_kategori','nama'])
    for k in KategoriPJU.query.filter_by(aktif=True).order_by(KategoriPJU.kode).all():refs.append([k.kode,k.nama])
    refs.append([]);refs.append(['kode_wilayah','kelurahan','kemantren'])
    for r in Wilayah.query.order_by(Wilayah.kode_wilayah).all():refs.append([r.kode_wilayah,r.nama_kelurahan,r.nama_kemantren])
    for name in ('Data_Aset','Data_Lampu'):
        w[name].freeze_panes='A2'
        for row in w[name].iter_rows(min_row=2,max_row=101,max_col=3 if name=='Data_Aset' else 1):
            for c in row:c.number_format='@'
    g=w.create_sheet('Panduan')
    for text in ['Satu baris satu aset; satu baris satu lampu. Hubungkan melalui kode_aset.','CSV hanya aset; Excel dua sheet. Sheet lampu boleh kosong.','Maksimum 4 MB sementara, 1000 baris total. Formula dilarang.','Status dan kategori jalan wajib; kategori dan wilayah harus sesuai master.']:
        g.append([text])
    b=io.BytesIO();w.save(b)
    return attachment(b.getvalue(),'template_import_pijar.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
