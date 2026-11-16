from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, func
from PIL import Image
from mutagen.mp3 import MP3
from mutagen.id3 import TALB,TPE2
from app.config import Settings
from app.main import create_app
from app.models.catalog import track,media_asset,track_description,description_revision,processing_job,favorite
from app.services import processing
from app.integrations.storage import MediaStore

pytestmark=[pytest.mark.integration,pytest.mark.anyio]

@pytest.fixture
async def client(catalog_engine,tmp_path):
    app=create_app(Settings(_env_file=None,media_root=tmp_path/'media'))
    original=app.state.database_engine;app.state.database_engine=catalog_engine
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://localhost') as client:
        yield client,app
    if original is not None: original.dispose()

def audio():
    stream=BytesIO(Path('/app/fixtures/sin_etiquetas.mp3').read_bytes());mp3=MP3(stream);mp3.add_tags();mp3.tags.add(TALB(encoding=3,text=['Álbum de etiquetas']));mp3.tags.add(TPE2(encoding=3,text=['Artista de etiquetas']));mp3.save(stream);return stream.getvalue()

async def folder(c,title='Mi carpeta',**extra):
    response=await c.post('/api/v1/albums',json={'title':title,'cover_asset_id':None,**extra});assert response.status_code==201;return response.json()

async def import_to(c,identity):
    r=await c.post(f'/api/v1/imports?album_id={identity}',files={'files':('test.mp3',audio(),'audio/mpeg')});assert r.status_code==200;return r.json()['results'][0]

async def test_album_cover_wall_and_destination_overrides_tags(client):
    c,_=client;out=BytesIO();Image.new('RGB',(32,32),'red').save(out,format='PNG')
    asset=(await c.post('/api/v1/assets',data={'purpose':'cover'},files={'file':('cover.png',out.getvalue(),'image/png')})).json()
    a=await folder(c,cover_asset_id=asset['id']);assert a['cover_asset_id']==asset['id'];assert a['metadata_sources']['cover']=='manual';assert (await c.get(f"/api/v1/albums/{a['id']}/wall")).status_code==200
    result=await import_to(c,a['id']);detail=(await c.get('/api/v1/tracks/'+result['track_id'])).json();assert detail['album_id']==a['id'];assert detail['metadata_sources']['album']=='manual'
    other=await folder(c,'Otra carpeta');duplicate=await import_to(c,other['id']);assert duplicate['status']=='duplicate';assert duplicate['destination_mismatch'];assert (await c.get('/api/v1/tracks/'+result['track_id'])).json()['album_id']==a['id']
    assert (await c.post(f'/api/v1/imports?album_id={uuid4()}',files={'files':('test.mp3',audio(),'audio/mpeg')})).status_code==404

async def test_delete_is_versioned_hides_everywhere_preserves_history_and_original(client,catalog_engine):
    c,app=client;a=await folder(c);result=await import_to(c,a['id']);identity=result['track_id'];url='/api/v1/tracks/'+identity
    await c.put(url+'/favorite',json={'favorite':True})
    p=await c.post('/api/v1/playlists',json={'name':'Lista'});p=await c.put('/api/v1/playlists/'+p.json()['id']+'/tracks',headers={'If-Match':p.headers['etag']},json={'track_ids':[identity]});playlist_id=p.json()['id'];old_playlist_etag=p.headers['etag']
    r=await c.put(url+'/description',headers={'If-None-Match':'*'},json={'text':'Ficha conservada','features':[],'source':'manual','source_details':'Anotación de prueba'});assert r.status_code==200
    await c.post(url+'/processing-jobs',json={'operation':'prepare_metadata'});claimed=processing.claim(catalog_engine);assert claimed is not None
    before=await c.get(url);assert (await c.delete(url)).status_code==428;assert (await c.delete(url,headers={'If-Match':'"wrong"'})).status_code==412
    removed=await c.delete(url,headers={'If-Match':before.headers['etag']});assert removed.status_code==200;assert removed.json()['original_preserved']
    from alembic import command
    from app.database import migration_config
    with pytest.raises(RuntimeError,match='canciones retiradas'):
        with catalog_engine.begin() as connection:
            config=migration_config();config.attributes['connection']=connection;command.downgrade(config,'0009_favorites')
    for suffix in ['', '/audio','/description','/favorite']:
        assert (await c.get(url+suffix)).status_code==404
    assert (await c.get('/api/v1/tracks')).json()['total']==0;assert (await c.get('/api/v1/favorites')).json()['total']==0;assert (await c.get('/api/v1/albums/'+a['id'])).json()['track_count']==0
    p=await c.get('/api/v1/playlists/'+playlist_id);assert p.json()['items']==[];assert p.headers['etag']!=old_playlist_etag
    assert processing.finish(catalog_engine,claimed,result={'track_revision':claimed.input_version}) is False
    with catalog_engine.connect() as connection:
        row=connection.execute(select(track).where(track.c.id==UUID(identity))).one();assert row.deleted_at is not None
        for table in [track_description,description_revision,favorite]:assert connection.scalar(select(func.count()).select_from(table))==1
        assert connection.execute(select(processing_job.c.status)).scalar_one()=='stale'
        asset=connection.execute(select(media_asset).where(media_asset.c.id==row.audio_asset_id)).one();assert MediaStore(app.state.settings.media_root).path_for(asset.storage_key).read_bytes()==audio()
    restored=await import_to(c,a['id']);assert restored['restored'];assert restored['track_id']==identity;assert (await c.get(url)).status_code==200;assert (await c.get(url+'/description')).json()['text']=='Ficha conservada'

async def test_deleted_track_rejected_by_playlist_edit(client):
    c,_=client;a=await folder(c);identity=(await import_to(c,a['id']))['track_id'];r=await c.get('/api/v1/tracks/'+identity);await c.delete('/api/v1/tracks/'+identity,headers={'If-Match':r.headers['etag']})
    p=await c.post('/api/v1/playlists',json={'name':'Prueba'});assert (await c.put('/api/v1/playlists/'+p.json()['id']+'/tracks',headers={'If-Match':p.headers['etag']},json={'track_ids':[identity]})).status_code==422
