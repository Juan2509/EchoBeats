package org.echobeats;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.springframework.dao.DataAccessException;
import org.springframework.http.CacheControl;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

import tools.jackson.databind.JsonNode;

@RestController
@RequestMapping("/api/v1/tracks/{trackId}/favorite")
class FavoriteController {
    private final FavoriteService favorites;

    FavoriteController(FavoriteService favorites) {
        this.favorites = favorites;
    }

    @GetMapping
    ResponseEntity<FavoriteState> get(@PathVariable UUID trackId) {
        return response(favorites.get(trackId));
    }

    @PutMapping
    ResponseEntity<?> put(@PathVariable UUID trackId, @RequestBody JsonNode body) {
        if (!body.isObject() || body.size() != 1 || !body.path("favorite").isBoolean()) {
            return invalidData();
        }
        return response(favorites.set(trackId, body.path("favorite").asBoolean()));
    }

    @ExceptionHandler({HttpMessageNotReadableException.class, MethodArgumentTypeMismatchException.class})
    ResponseEntity<?> invalidData() {
        return error(422, "invalid_data", "Revisa los campos enviados; hay datos vacíos, no válidos o no permitidos.");
    }

    @ExceptionHandler(FavoriteService.TrackNotFound.class)
    ResponseEntity<?> missingTrack() {
        return error(404, "track_not_found", "La canción no existe.");
    }

    @ExceptionHandler(DataAccessException.class)
    ResponseEntity<?> unavailable() {
        return error(503, "database_unavailable", "No se pudo completar la operación con la base de datos.");
    }

    private static ResponseEntity<FavoriteState> response(FavoriteState state) {
        return ResponseEntity.ok().cacheControl(CacheControl.noStore()).body(state);
    }

    private static ResponseEntity<?> error(int status, String code, String message) {
        return ResponseEntity.status(status).body(Map.of("error",
            Map.of("code", code, "message", message, "fields", List.of(), "request_id", UUID.randomUUID())));
    }

    record FavoriteState(UUID track_id, boolean favorite, OffsetDateTime created_at) {}
}
