package org.echobeats;

import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.springframework.dao.DataAccessException;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.ServletRequestBindingException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

final class ApiFailure extends RuntimeException {
    final int status;
    final String code;
    final Integer revision;
    final String etag;

    ApiFailure(int status, String code, String message) {
        this(status, code, message, null, null);
    }

    ApiFailure(int status, String code, String message, Integer revision, String etag) {
        super(message);
        this.status = status;
        this.code = code;
        this.revision = revision;
        this.etag = etag;
    }

    static String token(String kind, UUID id, int revision) {
        return "\"" + kind + "-" + id + "-" + revision + "\"";
    }

    static void requireRevision(String kind, UUID id, int revision, String expected) {
        if (expected == null) throw new ApiFailure(428, "revision_required",
            "Falta la revisión del recurso. Recarga los datos antes de guardar.");
        String current = token(kind,id,revision);
        if (!current.equals(expected)) throw new ApiFailure(412, "revision_conflict",
            "Los datos cambiaron en otra pestaña. Recarga para revisar tus cambios.",revision,current);
    }
}

@RestControllerAdvice
class ApiFailureHandler {
    @ExceptionHandler(ApiFailure.class)
    ResponseEntity<?> failure(ApiFailure failure) {
        if (failure.etag != null) {
            return ResponseEntity.status(failure.status).eTag(failure.etag).header("Cache-Control","no-store")
                .body(Map.of("error",Map.of("code",failure.code,"message",failure.getMessage(),
                    "current_revision",failure.revision,"current_etag",failure.etag)));
        }
        return ResponseEntity.status(failure.status).body(Map.of("error", Map.of(
            "code", failure.code, "message", failure.getMessage(), "fields", List.of(),
            "request_id", UUID.randomUUID())));
    }

    @ExceptionHandler({MethodArgumentTypeMismatchException.class, ServletRequestBindingException.class,
        HttpMessageNotReadableException.class})
    ResponseEntity<?> invalid() {
        return failure(new ApiFailure(422, "invalid_data",
            "Revisa los campos enviados; hay datos vacíos, no válidos o no permitidos."));
    }

    @ExceptionHandler(DataAccessException.class)
    ResponseEntity<?> unavailable() {
        return failure(new ApiFailure(503, "database_unavailable",
            "No se pudo completar la operación con la base de datos."));
    }
}
