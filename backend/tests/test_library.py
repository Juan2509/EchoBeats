"""Búsqueda real aislada: relaciones, texto literal, orden y paginación."""
import pytest
from app.models.catalog import playlist

from test_metadata import client, tagged, upload  # reutiliza el entorno aislado de importación

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


async def test_empty_library_hides_only_empty_system_album(client):
    api, _ = client
    assert (await api.get('/api/v1/albums?include_empty_system=false')).json()['total'] == 0
    assert (await api.get('/api/v1/albums')).json()['total'] == 1
    await api.post('/api/v1/albums', json={'title': 'Álbum vacío'})
    found = (await api.get('/api/v1/albums?include_empty_system=false')).json()
    assert found['total'] == 1 and found['items'][0]['title'] == 'Álbum vacío'


async def test_search_by_title_album_and_artist_without_duplicate_rows(client, catalog_engine):
    api, _ = client
    item = await upload(api, tagged(title='Lluvia eléctrica', collection='Recuerdos', names=['Dúo Lunar', 'Otro artista']))
    for query in ['LLUVIA', 'recuerdos', 'DÚO LUNAR', 'Otro artista']:
        songs = (await api.get('/api/v1/tracks', params={'q': query})).json()
        albums = (await api.get('/api/v1/albums', params={'q': query})).json()
        assert songs['total'] == albums['total'] == 1
        assert songs['items'][0]['id'] == item['track_id']
        assert albums['items'][0]['id'] == songs['items'][0]['album_id']
    assert (await api.get('/api/v1/tracks', params={'q': 'electrica'})).json()['total'] == 0
    groups = (await api.get('/api/v1/library/search', params={'q': '  lluvia  '})).json()
    assert groups['query'] == 'lluvia'
    assert groups['tracks']['total'] == groups['albums']['total'] == 1
    assert groups['playlists']['items'] == []
    with catalog_engine.begin() as connection:
        connection.execute(playlist.insert(), [{'name': f'Lluvia {index:02}'} for index in range(12)])
    groups = (await api.get('/api/v1/library/search', params={'q': 'lluvia'})).json()
    assert groups['playlists']['total'] == 12 and len(groups['playlists']['items']) == 10
    assert 'vista=playlists' in groups['playlists']['href']
    assert 'vista=canciones' in groups['tracks']['href']


async def test_literal_search_and_pagination(client):
    api, _ = client
    await upload(api, tagged(title='100%_real\\', collection='Pruebas'))
    await upload(api, tagged(title='Otra canción', collection='Pruebas'))
    for query in ['%', '_', '\\']:
        found = (await api.get('/api/v1/tracks', params={'q': query})).json()
        assert found['total'] == 1 and found['items'][0]['title'] == '100%_real\\'
    first = (await api.get('/api/v1/tracks', params={'limit': 1})).json()
    second = (await api.get('/api/v1/tracks', params={'limit': 1, 'offset': 1})).json()
    assert first['total'] == second['total'] == 2
    assert first['items'][0]['id'] != second['items'][0]['id']
    assert (await api.get('/api/v1/tracks', params={'offset': 100})).json()['items'] == []
    assert (await api.get('/api/v1/albums', params={'q': "' OR 1=1 --"})).json()['total'] == 0


async def test_album_tracks_order_and_filter(client):
    api, _ = client
    first = await upload(api, tagged(title='Zeta', collection='Orden'))
    second = await upload(api, tagged(title='Alfa', collection='Orden'))
    url = f"/api/v1/tracks/{first['track_id']}"
    response = await api.get(url)
    album_id = response.json()['album_id']
    await api.patch(url, headers={'If-Match': response.headers['etag']}, json={'track_number': 1})
    songs = (await api.get('/api/v1/tracks', params={'album_id': album_id})).json()
    assert [row['id'] for row in songs['items']] == [first['track_id'], second['track_id']]
    assert (await api.get('/api/v1/tracks', params={'album_id': album_id, 'q': 'Alfa'})).json()['total'] == 1
