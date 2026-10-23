"""Publica solo HTML verticales vigentes; respeta plazos y permanencia."""
from pathlib import Path
from datetime import datetime, timezone, timedelta, date
import re
import shutil

PATTERN = re.compile(r'vertical-mickey-[a-z0-9][a-z0-9-]{0,46}\.html')
MARKER = re.compile(r'<meta name="invitation-event-date" content="(\d{4}-\d{2}-\d{2})">')

def read_expiry(event_date, header=''):
    marker=re.search(r'<meta name="invitation-expiry-date" content="([^"]*)">',header)
    if not marker:
        if 'name="invitation-expiry-date"' in header:raise ValueError('Marcador de vigencia inválido.')
        return date.fromisoformat(event_date)+timedelta(days=30)
    if marker.group(1)=='never':return None
    expiry=date.fromisoformat(marker.group(1))
    if expiry<date.fromisoformat(event_date):raise ValueError('La retirada no puede ser anterior al evento.')
    return expiry

def prepare(root, today=None):
    root=Path(root).resolve()
    today=today or datetime.now(timezone(timedelta(hours=-5))).date()
    entries=[]
    for path in root.glob('vertical-*.html'):
        if path.is_symlink() or not path.is_file() or not PATTERN.fullmatch(path.name):
            raise ValueError('Archivo no permitido: '+path.name)
        head=path.read_text(encoding='utf-8').split('</head>',1)[0]
        marker=MARKER.search(head)
        if not marker:raise ValueError('Falta fecha de evento: '+path.name)
        entries.append((path,read_expiry(marker.group(1),head)))
    output=root/'_site'
    if output.is_symlink():raise ValueError('_site no puede ser un enlace.')
    if output.exists() and any(p.is_symlink() or not p.is_file() for p in output.iterdir()):
        raise ValueError('Contenido inesperado en _site.')
    output.mkdir(exist_ok=True)
    for old in output.iterdir():old.unlink()
    retired=[]
    for path,expires in entries:
        if expires is not None and today>=expires:
            path.unlink()
            retired.append(path.name)
        else:shutil.copyfile(path,output/path.name)
    (output/'index.html').write_text('<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Invitaciones</title><p>Abre el enlace de tu invitación para conocer los detalles.</p></html>',encoding='utf-8')
    (output/'.nojekyll').touch()
    print('Fecha de Perú:',today,'· Retiradas:',retired)
    return retired

if __name__=='__main__':prepare(Path(__file__).resolve().parent)
