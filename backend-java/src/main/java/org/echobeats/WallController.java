package org.echobeats;

import java.util.UUID;

import org.springframework.http.CacheControl;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import tools.jackson.databind.JsonNode;

@RestController
@RequestMapping("/api/v1/albums/{albumId}/wall")
class WallController {
    private final WallService walls;

    WallController(WallService walls) {
        this.walls = walls;
    }

    @GetMapping
    ResponseEntity<JsonNode> get(@PathVariable UUID albumId) {
        return response(walls.get(albumId));
    }

    @PutMapping
    ResponseEntity<JsonNode> put(@PathVariable UUID albumId, @RequestBody JsonNode body,
                                 @RequestHeader(name="If-Match",required=false) String expected) {
        return response(walls.replace(albumId, WallService.Composition.parse(body), expected));
    }

    @PostMapping("/reset")
    ResponseEntity<JsonNode> reset(@PathVariable UUID albumId,
                                   @RequestHeader(name="If-Match",required=false) String expected) {
        return response(walls.replace(albumId, WallService.Composition.initial(), expected));
    }

    private static ResponseEntity<JsonNode> response(JsonNode wall) {
        return ResponseEntity.ok().cacheControl(CacheControl.noStore())
            .eTag(ApiFailure.token("wall",UUID.fromString(wall.path("id").asString()),wall.path("revision").asInt()))
            .body(wall);
    }
}
