package org.echobeats;

import java.time.OffsetDateTime;
import java.util.UUID;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Transactional;

import org.echobeats.FavoriteController.FavoriteState;

@Service
class FavoriteService {
    private final JdbcTemplate jdbc;

    FavoriteService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @Transactional(readOnly = true, isolation = Isolation.REPEATABLE_READ)
    public FavoriteState get(UUID trackId) {
        requireTrack(trackId, false);
        return state(trackId);
    }

    @Transactional
    public FavoriteState set(UUID trackId, boolean favorite) {
        requireTrack(trackId, true);
        if (favorite) {
            jdbc.update("INSERT INTO favorite (track_id) VALUES (?) ON CONFLICT DO NOTHING", trackId);
        } else {
            jdbc.update("DELETE FROM favorite WHERE track_id = ?", trackId);
        }
        return state(trackId);
    }

    private void requireTrack(UUID trackId, boolean lock) {
        String query = "SELECT id FROM track WHERE id = ? AND deleted_at IS NULL";
        if (lock) {
            query += " FOR UPDATE";
        }
        if (jdbc.queryForList(query, UUID.class, trackId).isEmpty()) {
            throw new TrackNotFound();
        }
    }

    private FavoriteState state(UUID trackId) {
        var timestamps = jdbc.query("SELECT created_at FROM favorite WHERE track_id = ?",
            (row, index) -> row.getObject(1, OffsetDateTime.class), trackId);
        return new FavoriteState(trackId, !timestamps.isEmpty(), timestamps.isEmpty() ? null : timestamps.getFirst());
    }

    static class TrackNotFound extends RuntimeException {}
}
