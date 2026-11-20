package org.echobeats;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Transactional;

import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;

@Service
@Transactional(readOnly = true, isolation = Isolation.REPEATABLE_READ)
class CatalogReader {
    private static final String TRACK_MATCH = """
        (t.title ILIKE :pattern OR EXISTS (
            SELECT 1 FROM track_artist c JOIN artist a ON a.id=c.artist_id
            WHERE c.track_id=t.id AND a.name ILIKE :pattern
        ) OR EXISTS (SELECT 1 FROM album a WHERE a.id=t.album_id AND a.title ILIKE :pattern)
          OR EXISTS (
            SELECT 1 FROM album_artist c JOIN artist a ON a.id=c.artist_id
            WHERE c.album_id=t.album_id AND a.name ILIKE :pattern
        ))
        """;
    private static final String TRACK = """
        SELECT jsonb_build_object(
          'id',t.id,'title',t.title,'content_sha256',t.content_sha256,
          'artists',COALESCE((SELECT jsonb_agg(jsonb_build_object('id',a.id,'name',a.name) ORDER BY c.position)
             FROM track_artist c JOIN artist a ON a.id=c.artist_id WHERE c.track_id=t.id),'[]'::jsonb),
          'album_id',t.album_id,'album_title',al.title,'duration_ms',t.duration_ms,
          'audio_url','/api/v1/tracks/'||t.id||'/audio','audio_mime_type',m.mime_type,
          'track_number',t.track_number,'cover_asset_id',t.cover_asset_id,
          'cover_url','/api/v1/assets/'||COALESCE(t.cover_asset_id,
             CASE WHEN t.metadata_sources->>'cover' IS DISTINCT FROM 'manual' THEN al.cover_asset_id END)||'/content',
          'cover_source',CASE WHEN t.cover_asset_id IS NULL AND al.cover_asset_id IS NOT NULL
             AND t.metadata_sources->>'cover' IS DISTINCT FROM 'manual' THEN 'album'
             ELSE COALESCE(t.metadata_sources->>'cover','fallback') END,
          'metadata_sources',t.metadata_sources,'revision',t.revision,'updated_at',t.updated_at)
        FROM track t JOIN album al ON al.id=t.album_id JOIN media_asset m ON m.id=t.audio_asset_id
        """;
    private static final String ALBUM = """
        SELECT jsonb_build_object('id',al.id,'title',al.title,
          'artists',COALESCE((SELECT jsonb_agg(jsonb_build_object('id',a.id,'name',a.name) ORDER BY c.position)
             FROM album_artist c JOIN artist a ON a.id=c.artist_id WHERE c.album_id=al.id),'[]'::jsonb),
          'cover_asset_id',al.cover_asset_id,'cover_url','/api/v1/assets/'||al.cover_asset_id||'/content',
          'track_count',(SELECT count(*) FROM track t WHERE t.album_id=al.id AND t.deleted_at IS NULL),
          'system_key',al.system_key,'metadata_sources',al.metadata_sources,'revision',al.revision)
        FROM album al
        """;
    private static final String PLAYLIST = """
        SELECT jsonb_build_object('id',p.id,'name',p.name,'appearance',p.appearance,'revision',p.revision,
          'image_asset_id',p.image_asset_id,'image_url','/api/v1/assets/'||p.image_asset_id||'/content',
          'track_count',(SELECT count(*) FROM playlist_track c JOIN track t ON t.id=c.track_id
             WHERE c.playlist_id=p.id AND t.deleted_at IS NULL))
        FROM playlist p
        """;
    private final NamedParameterJdbcTemplate jdbc;
    private final ObjectMapper json;

    CatalogReader(NamedParameterJdbcTemplate jdbc, ObjectMapper json) {
        this.jdbc = jdbc;
        this.json = json;
    }

    public Page tracks(int limit, int offset, String query, UUID albumId, boolean favorites) {
        String filter = " WHERE t.deleted_at IS NULL";
        if (albumId != null) filter += " AND t.album_id=:album";
        if (favorites) filter += " AND EXISTS (SELECT 1 FROM favorite f WHERE f.track_id=t.id)";
        if (!query.isEmpty()) filter += " AND " + TRACK_MATCH;
        String order = albumId == null ? "lower(t.title),t.id" : "t.track_number NULLS LAST,lower(t.title),t.id";
        return page(TRACK, "track t", filter, order, parameters(limit, offset, query).addValue("album", albumId));
    }

    public Page albums(int limit, int offset, String query, boolean includeEmptySystem) {
        String filter = " WHERE TRUE";
        if (!includeEmptySystem) filter += """
             AND (al.system_key IS NULL OR EXISTS
                 (SELECT 1 FROM track t WHERE t.album_id=al.id AND t.deleted_at IS NULL))
            """;
        if (!query.isEmpty()) filter += """
             AND (al.title ILIKE :pattern OR EXISTS (
                 SELECT 1 FROM album_artist c JOIN artist a ON a.id=c.artist_id
                 WHERE c.album_id=al.id AND a.name ILIKE :pattern
             ) OR EXISTS (
                 SELECT 1 FROM track t WHERE t.album_id=al.id AND t.deleted_at IS NULL AND %s
             ))
            """.formatted(TRACK_MATCH);
        return page(ALBUM, "album al", filter, "lower(al.title),al.id", parameters(limit, offset, query));
    }

    public Page playlists(int limit, int offset, String query) {
        String filter = query.isEmpty() ? "" : " WHERE p.name ILIKE :pattern";
        return page(PLAYLIST, "playlist p", filter, "lower(p.name),p.id", parameters(limit, offset, query));
    }

    public JsonNode track(UUID id) {
        return detail(TRACK + " WHERE t.id=:id AND t.deleted_at IS NULL", id, "track_not_found", "No existe esa canción.");
    }

    public JsonNode album(UUID id) {
        return detail(ALBUM + " WHERE al.id=:id", id, "album_not_found", "No existe ese álbum.");
    }

    public JsonNode playlist(UUID id) {
        var playlist = detail(PLAYLIST + " WHERE p.id=:id", id, "playlist_not_found", "No existe esa playlist.");
        var items = read(TRACK + """
             JOIN playlist_track c ON c.track_id=t.id
             WHERE c.playlist_id=:id AND t.deleted_at IS NULL ORDER BY c.position
            """, new MapSqlParameterSource("id", id));
        var detail = json.createObjectNode();
        playlist.properties().forEach(field -> detail.set(field.getKey(), field.getValue()));
        detail.set("items", json.valueToTree(items));
        return detail;
    }

    public Map<String, Object> search(String query) {
        String encoded = URLEncoder.encode(query, StandardCharsets.UTF_8);
        return Map.of("query", query,
            "tracks", tracks(10, 0, query, null, false).linked("canciones", encoded),
            "albums", albums(10, 0, query, true).linked("albumes", encoded),
            "playlists", playlists(10, 0, query).linked("playlists", encoded));
    }

    private Page page(String select, String table, String filter, String order, MapSqlParameterSource parameters) {
        long total = jdbc.queryForObject("SELECT count(*) FROM " + table + filter, parameters, Long.class);
        var items = read(select + filter + " ORDER BY " + order + " LIMIT :limit OFFSET :offset", parameters);
        return new Page(items, total, (int) parameters.getValue("limit"), (int) parameters.getValue("offset"));
    }

    private JsonNode detail(String sql, UUID id, String code, String message) {
        var results = read(sql, new MapSqlParameterSource("id", id));
        if (results.isEmpty()) throw new ApiFailure(404, code, message);
        return results.getFirst();
    }

    private List<JsonNode> read(String sql, MapSqlParameterSource parameters) {
        return jdbc.query(sql, parameters, (row, index) -> json.readTree(row.getString(1)));
    }

    private static MapSqlParameterSource parameters(int limit, int offset, String query) {
        String literal = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_");
        return new MapSqlParameterSource().addValue("limit", limit).addValue("offset", offset)
            .addValue("pattern", "%" + literal + "%");
    }

    record Page(List<JsonNode> items, long total, int limit, int offset) {
        Map<String, Object> linked(String view, String query) {
            return Map.of("items", items, "total", total, "limit", limit, "offset", offset,
                "href", "/biblioteca?vista=" + view + "&q=" + query);
        }
    }
}
