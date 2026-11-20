package org.echobeats;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

import org.springframework.dao.DataAccessException;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1")
class HealthController {
    private static final Set<String> EXPECTED_SCHEMA = Set.of("0011_wall_full_size");
    private final JdbcTemplate jdbc;

    HealthController(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @GetMapping("/health")
    Map<String, String> health() {
        return Map.of("status", "ok");
    }

    @GetMapping("/ready")
    ResponseEntity<Readiness> readiness() {
        var checks = new LinkedHashMap<String, String>();
        checks.put("database", "unavailable");
        checks.put("pgvector", "unknown");
        checks.put("migrations", "unknown");
        try {
            jdbc.queryForObject("SELECT 1", Integer.class);
            checks.put("database", "ok");
            var vector = jdbc.queryForObject(
                "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')", Boolean.class);
            checks.put("pgvector", Boolean.TRUE.equals(vector) ? "ok" : "missing");
            var hasVersionTable = jdbc.queryForObject(
                "SELECT to_regclass('public.alembic_version') IS NOT NULL", Boolean.class);
            var revisions = Boolean.TRUE.equals(hasVersionTable)
                ? Set.copyOf(jdbc.queryForList("SELECT version_num FROM public.alembic_version", String.class))
                : Set.<String>of();
            checks.put("migrations", EXPECTED_SCHEMA.equals(revisions) ? "ok" : "pending");
        } catch (DataAccessException exception) {
            checks.put("database", "unavailable");
        }
        boolean available = checks.values().stream().allMatch("ok"::equals);
        return ResponseEntity.status(available ? 200 : 503)
            .body(new Readiness(available ? "ready" : "not_ready", checks));
    }

    record Readiness(String status, Map<String, String> checks) {}
}
