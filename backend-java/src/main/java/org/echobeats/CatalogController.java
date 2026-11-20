package org.echobeats;

import java.util.Map;
import java.util.UUID;

import org.springframework.http.CacheControl;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import tools.jackson.databind.JsonNode;

@RestController
@RequestMapping("/api/v1")
class CatalogController {
    private final CatalogReader catalog;
    private final PlaylistService playlists;

    CatalogController(CatalogReader catalog,PlaylistService playlists) {
        this.catalog = catalog;
        this.playlists = playlists;
    }

    @GetMapping("/tracks")
    CatalogReader.Page tracks(@RequestParam(defaultValue = "24") int limit, @RequestParam(defaultValue = "0") int offset,
                             @RequestParam(defaultValue = "") String q, @RequestParam(name = "album_id", required = false) UUID albumId) {
        return catalog.tracks(limit, offset, validate(limit, offset, q), albumId, false);
    }

    @GetMapping("/favorites")
    ResponseEntity<CatalogReader.Page> favorites(@RequestParam(defaultValue = "24") int limit,
                                               @RequestParam(defaultValue = "0") int offset,
                                               @RequestParam(defaultValue = "") String q) {
        return ResponseEntity.ok().cacheControl(CacheControl.noStore())
            .body(catalog.tracks(limit, offset, validate(limit, offset, q), null, true));
    }

    @GetMapping("/albums")
    CatalogReader.Page albums(@RequestParam(defaultValue = "24") int limit, @RequestParam(defaultValue = "0") int offset,
                             @RequestParam(defaultValue = "") String q,
                             @RequestParam(name = "include_empty_system", defaultValue = "true") boolean includeEmptySystem) {
        return catalog.albums(limit, offset, validate(limit, offset, q), includeEmptySystem);
    }

    @GetMapping("/playlists")
    CatalogReader.Page playlists(@RequestParam(defaultValue = "24") int limit, @RequestParam(defaultValue = "0") int offset,
                                @RequestParam(defaultValue = "") String q) {
        return catalog.playlists(limit, offset, validate(limit, offset, q));
    }

    @GetMapping("/library/search")
    Map<String, Object> search(@RequestParam String q) {
        String query = validate(10, 0, q);
        if (query.isEmpty()) throw new ApiFailure(422, "invalid_query", "Escribe un texto para buscar.");
        return catalog.search(query);
    }

    @GetMapping("/tracks/{id}")
    ResponseEntity<JsonNode> track(@PathVariable UUID id) {
        return detail("track", id, catalog.track(id));
    }

    @GetMapping("/albums/{id}")
    ResponseEntity<JsonNode> album(@PathVariable UUID id) {
        return detail("album", id, catalog.album(id));
    }

    @GetMapping("/playlists/{id}")
    ResponseEntity<JsonNode> playlist(@PathVariable UUID id) {
        return detail("playlist", id, catalog.playlist(id));
    }

    @PostMapping("/playlists")
    ResponseEntity<JsonNode> createPlaylist(@RequestBody JsonNode body) {
        var playlist=playlists.create(body);
        UUID id=UUID.fromString(playlist.path("id").asString());
        return ResponseEntity.status(201).cacheControl(CacheControl.noStore())
            .eTag(ApiFailure.token("playlist",id,playlist.path("revision").asInt())).body(playlist);
    }

    @PatchMapping("/playlists/{id}")
    ResponseEntity<JsonNode> editPlaylist(@PathVariable UUID id,@RequestBody JsonNode body,
                                          @RequestHeader(name="If-Match",required=false) String expected) {
        return detail("playlist",id,playlists.edit(id,body,expected));
    }

    @PutMapping("/playlists/{id}/tracks")
    ResponseEntity<JsonNode> replacePlaylistTracks(@PathVariable UUID id,@RequestBody JsonNode body,
                                                   @RequestHeader(name="If-Match",required=false) String expected) {
        return detail("playlist",id,playlists.tracks(id,body,expected));
    }

    private static String validate(int limit, int offset, String query) {
        String trimmed = query.strip();
        if (limit < 1 || limit > 100 || offset < 0 || trimmed.codePointCount(0, trimmed.length()) > 200
            || trimmed.indexOf(0) >= 0) {
            throw new ApiFailure(422, "invalid_data", "Revisa los campos enviados; hay datos vacíos, no válidos o no permitidos.");
        }
        return trimmed;
    }

    private static ResponseEntity<JsonNode> detail(String kind, UUID id, JsonNode record) {
        return ResponseEntity.ok().cacheControl(CacheControl.noStore())
            .eTag(ApiFailure.token(kind,id,record.path("revision").asInt())).body(record);
    }
}
