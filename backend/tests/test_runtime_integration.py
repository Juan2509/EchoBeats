"""P26: HTTP real, procesos nuevos y medios/BD aislados; no es escucha ni API real."""
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from io import BytesIO
from anyio import to_thread
from httpx import AsyncClient, Client
from PIL import Image
import pytest
from app.integrations.ai import AIError
from app.media_audit import audit
from app.integrations.storage import MediaStore
from test_metadata import FIXTURES, client, tagged, png
from test_walls import composition, element
from test_search import add, enable, vec, Fake

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


async def test_recreated_settings_keep_temporary_media_and_private_key_disabled(client, tmp_path):
    from app.config import Settings
    from test_indexing import config
    api, app = client
    expected = tmp_path / 'media'
    settings = Settings(_env_file=None)
    assert settings.media_root == expected and not settings.ai_enabled
    assert not settings.openai_api_key.get_secret_value() and not settings.processing_worker_enabled
    assert config().media_root == expected
    enabled, _ = enable(app)
    assert enabled.media_root == expected
    identity = (await api.post('/api/v1/imports',files={'files':('aislada.mp3',tagged(),'audio/mpeg')})).json()['results'][0]['track_id']
    assert (await api.get(f'/api/v1/tracks/{identity}/audio')).status_code == 200
    assert len(list((expected / 'audio').glob('*.mp3'))) == 1


class IsolatedServer:
    def __init__(self, engine, root):
        name = engine.url.database
        assert re.fullmatch(r'echobeats_test_[0-9a-f]{32}', name)
        self.port_file = root / 'port.txt'
        self.media = root / 'media'
        self.env = {**os.environ, 'P26_DATABASE': name, 'P26_MEDIA': str(self.media),
            'P26_PORT_FILE': str(self.port_file), 'DATABASE_URL': '',
            'POSTGRES_DB': name, 'MEDIA_ROOT': str(self.media),
            'PYTHONPATH': str(Path(__file__).resolve().parents[1]),
            'POSTGRES_HOST': engine.url.host, 'POSTGRES_PORT': str(engine.url.port or 5432),
            'POSTGRES_USER': engine.url.username, 'POSTGRES_PASSWORD': engine.url.password,
            'AI_ENABLED': 'false', 'OPENAI_API_KEY': '', 'PROCESSING_WORKER_ENABLED': 'false'}
        self.process = None
        self.url = ''

    def start(self):
        self.port_file.unlink(missing_ok=True)
        self.process = subprocess.Popen([sys.executable, str(Path(__file__).with_name('runtime_server.py'))],
            env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.monotonic() + 20
        with Client(timeout=.5, trust_env=False) as probe:
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise AssertionError(f'El servidor aislado terminó antes de ready (código {self.process.returncode}).')
                if self.port_file.exists():
                    self.url = 'http://127.0.0.1:' + self.port_file.read_text(encoding='ascii')
                    try:
                        if probe.get(self.url + '/api/v1/ready').status_code == 200:
                            return self.process.pid
                    except Exception:
                        pass
                time.sleep(.1)
        self.stop()
        raise AssertionError('El servidor aislado no alcanzó ready dentro del límite.')

    def stop(self):
        if self.process is None: return
        if self.process.poll() is None:
            self.process.terminate()
            try: self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill(); self.process.wait(timeout=5)


def gif():
    output = BytesIO()
    a, b = Image.new('RGB', (30,30), 'red'), Image.new('RGB', (30,30), 'blue')
    a.save(output, format='GIF', save_all=True, append_images=[b], duration=100, loop=0)
    return output.getvalue()


async def test_real_http_restart_preserves_import_metadata_playlist_walls_assets_and_reset(catalog_engine, tmp_path):
    server = IsolatedServer(catalog_engine, tmp_path)
    original = (FIXTURES / 'sin_etiquetas.mp3').read_bytes()
    snapshots = {}
    try:
        first_pid = await to_thread.run_sync(server.start)
        async with AsyncClient(base_url=server.url, timeout=15, trust_env=False) as api:
            assert (await api.get('/api/v1/tracks')).json()['total'] == 0
            imported = await api.post('/api/v1/imports', files=[
                ('files', ('sin_etiquetas.mp3', original, 'audio/mpeg')),
                ('files', ('otro.mp3', tagged(title='Otra', collection='Álbum B'), 'audio/mpeg')),
                ('files', ('incorrecto.mp3', b'no es audio', 'audio/mpeg'))])
            assert imported.status_code == 200, imported.text
            rows = imported.json()['results']
            assert [r['status'] for r in rows] == ['imported','imported','rejected']
            a,b = rows[0]['track_id'],rows[1]['track_id']
            raw = await api.get(f'/api/v1/tracks/{a}')
            assert raw.json()['metadata_sources']['title'] == 'fallback' and raw.json()['cover_url'] is None
            album = await api.post('/api/v1/albums',json={'title':'Álbum A'})
            edited = await api.patch(f'/api/v1/tracks/{a}',headers={'If-Match':raw.headers['etag']},
                json={'title':'Corregida','artist_names':['Autor local'],'album_id':album.json()['id']})
            assert edited.status_code == 200, edited.text
            assert edited.json()['metadata_sources']['title']=='manual'
            assert edited.json()['title']=='Corregida' and edited.json()['artists'][0]['name']=='Autor local'
            duplicate = await api.post('/api/v1/imports',files={'files':('copia.mp3',original,'audio/mpeg')})
            assert duplicate.json()['results'][0]['status']=='duplicate'
            assert duplicate.json()['results'][0]['track_id']==a
            assert (await api.get(f'/api/v1/tracks/{a}')).json()==edited.json()
            other = (await api.get(f'/api/v1/tracks/{b}')).json()
            for query in ['Corregida','Autor local','Álbum A']:
                assert (await api.get('/api/v1/tracks',params={'q':query})).json()['items'][0]['id']==a
            assert (await api.get('/api/v1/tracks',params={'q':'NO_EXISTE_P26'})).json()['total']==0
            playlist = await api.post('/api/v1/playlists',json={'name':'Antes'})
            purl = '/api/v1/playlists/'+playlist.json()['id']
            ordered = await api.put(purl+'/tracks',headers={'If-Match':playlist.headers['etag']},json={'track_ids':[b,a]})
            cover = await api.post('/api/v1/assets',files={'file':('portada.png',png(),'image/png')},data={'purpose':'playlist'})
            changed = await api.patch(purl,headers={'If-Match':ordered.headers['etag']},json={'name':'Después','appearance':'image','image_asset_id':cover.json()['id']})
            assert changed.status_code==200,changed.text
            bad_image = await api.post('/api/v1/assets',files={'file':('rota.png',b'rota','image/png')},data={'purpose':'playlist'})
            assert bad_image.status_code==422 and (await api.get(purl)).json()==changed.json()
            image = await api.post('/api/v1/assets',files={'file':('objeto.png',png(),'image/png')},data={'purpose':'wall'})
            animated = await api.post('/api/v1/assets',files={'file':('objeto.gif',gif(),'image/gif')},data={'purpose':'wall'})
            assert image.status_code==animated.status_code==201
            wa=f"/api/v1/albums/{edited.json()['album_id']}/wall"
            wb=f"/api/v1/albums/{other['album_id']}/wall"
            initial_a, initial_b = await api.get(wa), await api.get(wb)
            avalue=composition(element(image.json()['id'],cx=.35,rotation_deg=30,z_index=1),
                element(animated.json()['id'],kind='gif',cx=.65,rotation_deg=-20,z_index=0),color='#123456')
            bvalue=composition(element(image.json()['id'],rotation_deg=0),color='#654321')
            saved_a=await api.put(wa,headers={'If-Match':initial_a.headers['etag']},json=avalue)
            saved_b=await api.put(wb,headers={'If-Match':initial_b.headers['etag']},json=bvalue)
            assert saved_a.status_code==saved_b.status_code==200
            assert (await api.get(wa)).json()==saved_a.json()
            # Respuesta/revisión de otro álbum nunca autoriza una escritura en A.
            assert (await api.put(wa,headers={'If-Match':saved_b.headers['etag']},json=avalue)).status_code==412
            invalid=composition(element(image.json()['id'],width=.99))
            assert (await api.put(wa,headers={'If-Match':saved_a.headers['etag']},json=invalid)).status_code==422
            assert (await api.get(wa)).json()==saved_a.json()
            favorite_url=f'/api/v1/tracks/{a}/favorite'
            assert (await api.put(favorite_url,json={'favorite':True})).status_code==200
            for url in [f'/api/v1/tracks/{a}',f'/api/v1/tracks/{b}',purl,wa,wb,favorite_url]:
                response=await api.get(url);snapshots[url]=(response.json(),response.headers.get('etag'))
            resource_urls=[changed.json()['image_url']]
            for value in [saved_a.json(),saved_b.json()]:
                for obj in value['elements']:
                    resource_urls.append(obj['content_url'])
                    if obj['static_preview_url']:
                        resource_urls.append(obj['static_preview_url'])
            resources={}
            for url in resource_urls:
                resource=await api.get(url)
                assert resource.status_code==200 and resource.headers['content-type'] in {'image/png','image/jpeg','image/gif'}
                with Image.open(BytesIO(resource.content)) as decoded:
                    decoded.verify()
                resources[url]=resource.content
            audio_url=f'/api/v1/tracks/{a}/audio'
            audio=await api.get(audio_url)
            assert audio.content==original
            audio_etag=audio.headers['etag']
        await to_thread.run_sync(server.stop)
        second_pid=await to_thread.run_sync(server.start)
        assert first_pid!=second_pid
        async with AsyncClient(base_url=server.url,timeout=15,trust_env=False) as api:
            for url,(data,etag) in snapshots.items():
                response=await api.get(url)
                assert response.status_code==200 and response.json()==data and response.headers.get('etag')==etag
            for url,content in resources.items():
                assert (await api.get(url)).content==content
            for start,stop in [(0,32),(1000,1200),(len(original)-128,len(original))]:
                ranged=await api.get(audio_url,headers={'Range':f'bytes={start}-{stop-1}','If-Range':audio_etag})
                assert ranged.status_code==206 and ranged.content==original[start:stop]
            assert (await api.head(audio_url)).headers['content-length']==str(len(original))
            assert (await api.get(audio_url,headers={'Range':f'bytes={len(original)}-'})).status_code==416
            reset=await api.post(wa+'/reset',headers={'If-Match':snapshots[wa][1]})
            assert reset.status_code==200,reset.text
            reset_data=reset.json()
            assert reset_data['elements']==[] and (await api.get(wb)).json()==snapshots[wb][0]
            assert (await api.put(favorite_url,json={'favorite':False})).status_code==200
        await to_thread.run_sync(server.stop)
        await to_thread.run_sync(server.start)
        async with AsyncClient(base_url=server.url,timeout=15,trust_env=False) as api:
            assert (await api.get(wa)).json()==reset_data
            assert (await api.get(wb)).json()==snapshots[wb][0]
            assert (await api.get(favorite_url)).json()['favorite'] is False
            assert (await api.get(audio_url)).content==original
            assert (await api.get(purl)).json()==snapshots[purl][0]
        result=audit(catalog_engine,MediaStore(server.media))
        assert result['missing_asset_ids']==result['unreferenced_files']==result['staging_files']==[]
    finally:
        await to_thread.run_sync(server.stop)


@pytest.mark.parametrize('code',['ai_quota','ai_timeout','ai_invalid_response'])
async def test_provider_failure_then_recovery_keeps_catalog_audio_and_preferences_usable(client,catalog_engine,code):
    api,app=client;settings,_=enable(app)
    identity,_=await add(api,catalog_engine,settings,'Recuperación','Tono con fuente.',vec(1))
    url=f'/api/v1/tracks/{identity}'
    before=await api.get(url)
    playlist=await api.post('/api/v1/playlists',json={'name':'Conservar'})
    purl='/api/v1/playlists/'+playlist.json()['id']
    await api.put(purl+'/tracks',headers={'If-Match':playlist.headers['etag']},json={'track_ids':[str(identity)]})
    await api.put(url+'/favorite',json={'favorite':True})
    pbefore=(await api.get(purl)).json()
    original=(await api.get(url+'/audio')).content
    class Failure(Fake):
        async def embed(self,query):
            assert catalog_engine.pool.checkedout()==0
            raise AIError(code)
    app.state.ai_provider=Failure(settings)
    failed=await api.post('/api/v1/explore/search',json={'query':'tono','mode':'semantic'})
    assert failed.status_code==(504 if code=='ai_timeout' else 503)
    assert failed.json()['error']['code']==code
    assert (await api.get(url)).json()==before.json()
    assert (await api.get(purl)).json()==pbefore
    partial=await api.get(url+'/audio',headers={'Range':'bytes=100-199'})
    assert partial.status_code==206 and partial.content==original[100:200]
    assert (await api.get(url+'/favorite')).json()['favorite'] is True
    # Fallo de proveedor no afecta búsqueda textual ni exige repetir la fallida.
    local=await api.post('/api/v1/explore/search',json={'query':'tono','mode':'lexical','preferences':'favorites'})
    assert local.status_code==200 and local.json()['results'][0]['track']['id']==str(identity)
    app.state.ai_provider=Fake(settings)
    recovered=await api.post('/api/v1/explore/search',json={'query':'tono','mode':'semantic'})
    assert recovered.status_code==200 and recovered.json()['results'][0]['track']['id']==str(identity)
