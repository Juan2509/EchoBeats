package org.echobeats;

import java.io.EOFException;
import java.io.IOException;
import java.io.OutputStream;
import java.io.RandomAccessFile;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.regex.Pattern;

import jakarta.servlet.http.HttpServletRequest;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpRange;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

@RestController
@RequestMapping("/api/v1")
class MediaController {
    private static final Pattern KEY = Pattern.compile("(audio|images)/[a-f0-9]{32}\\.([a-z0-9]+)");
    private static final Map<String, String> MIME = Map.ofEntries(
        Map.entry("mp3","audio/mpeg"), Map.entry("wav","audio/wav"), Map.entry("flac","audio/flac"),
        Map.entry("ogg","audio/ogg"), Map.entry("opus","audio/ogg"), Map.entry("png","image/png"),
        Map.entry("jpg","image/jpeg"), Map.entry("jpeg","image/jpeg"), Map.entry("gif","image/gif"));
    private final JdbcTemplate jdbc;
    private final Path mediaRoot;

    MediaController(JdbcTemplate jdbc, @Value("${echobeats.media-root}") String mediaRoot) {
        this.jdbc = jdbc;
        this.mediaRoot = Path.of(mediaRoot).toAbsolutePath();
    }

    @RequestMapping(path="/tracks/{id}/audio", method={RequestMethod.GET, RequestMethod.HEAD})
    ResponseEntity<StreamingResponseBody> audio(@PathVariable UUID id, HttpServletRequest request) {
        var asset = resource("""
            SELECT a.* FROM media_asset a JOIN track t ON t.audio_asset_id=a.id
            WHERE t.id=? AND t.deleted_at IS NULL
            """, id, new ApiFailure(404, "track_not_found", "No existe esa canción."));
        return serve(asset, true, request);
    }

    @RequestMapping(path="/assets/{id}/content", method={RequestMethod.GET, RequestMethod.HEAD})
    ResponseEntity<StreamingResponseBody> visual(@PathVariable UUID id, HttpServletRequest request) {
        var asset = resource("""
            SELECT * FROM media_asset WHERE id=? AND (
                (kind IN ('cover','image') AND mime_type IN ('image/png','image/jpeg'))
                OR (kind='gif' AND mime_type='image/gif'))
            """, id, new ApiFailure(404,"cover_not_found","No existe esa portada."));
        return serve(asset, false, request);
    }

    private Asset resource(String sql, UUID id, ApiFailure absent) {
        var found = jdbc.query(sql, (r, i) -> new Asset(r.getString("kind"), r.getString("storage_key"),
            r.getString("mime_type"), r.getLong("byte_size"), r.getString("sha256")), id);
        if (found.isEmpty()) throw absent;
        return found.getFirst();
    }

    private ResponseEntity<StreamingResponseBody> serve(Asset asset, boolean audio, HttpServletRequest request) {
        var matcher = KEY.matcher(asset.key);
        if (!matcher.matches() || !(audio ? asset.kind.equals("audio") && matcher.group(1).equals("audio")
            : List.of("cover","image","gif").contains(asset.kind) && matcher.group(1).equals("images"))
            || !asset.mime.equals(MIME.get(matcher.group(2)))) throw missing(audio);

        Path file;
        BasicFileAttributes info;
        try {
            Path root = mediaRoot.toRealPath();
            Path candidate = root.resolve(asset.key);
            if (Files.isSymbolicLink(candidate)) throw missing(audio);
            file = candidate.toRealPath();
            if (!file.startsWith(root)) throw missing(audio);
            info = Files.readAttributes(file, BasicFileAttributes.class);
            if (!info.isRegularFile() || info.size() != asset.size) throw missing(audio);
            try (var verify = Files.newByteChannel(file)) {
                if (verify.size() != asset.size) throw missing(audio);
            }
        } catch (NoSuchFileException exception) {
            throw missing(audio);
        } catch (IOException exception) {
            throw new ApiFailure(503, "media_unavailable", "No se pudo acceder al archivo. Vuelve a intentarlo más tarde.");
        }

        var headers = new HttpHeaders();
        headers.set(HttpHeaders.CONTENT_TYPE, asset.mime);
        if (audio) headers.set(HttpHeaders.CONTENT_DISPOSITION, "inline");
        headers.set(HttpHeaders.CACHE_CONTROL, audio ? "private, no-cache" : "private, max-age=3600");
        headers.set("X-Content-Type-Options", "nosniff");
        headers.set(HttpHeaders.ACCEPT_RANGES, "bytes");
        headers.setETag("\"" + asset.sha256 + "\"");
        headers.setLastModified(info.lastModifiedTime().toInstant());
        String range = request.getHeader(HttpHeaders.RANGE);
        String ifRange = request.getHeader(HttpHeaders.IF_RANGE);
        if (request.getMethod().equals("HEAD")) {
            headers.setContentLength(asset.size);
            return ResponseEntity.ok().headers(headers).build();
        }
        if (range == null || (ifRange != null && !ifRange.equals(headers.getETag())
            && !ifRange.equals(headers.getFirst(HttpHeaders.LAST_MODIFIED)))) {
            headers.setContentLength(asset.size);
            return ResponseEntity.ok().headers(headers).body((StreamingResponseBody) out -> {
                try (var input = Files.newInputStream(file)) { input.transferTo(out); }
            });
        }
        return partial(file, asset, headers, range);
    }

    private static ResponseEntity<StreamingResponseBody> partial(Path file, Asset asset, HttpHeaders headers, String range) {
        List<HttpRange> ranges;
        try {
            ranges = HttpRange.parseRanges(range);
            if (ranges.isEmpty()) throw new IllegalArgumentException();
        } catch (IllegalArgumentException exception) {
            return ResponseEntity.badRequest().header(HttpHeaders.CONTENT_TYPE,"text/plain; charset=utf-8")
                .body(out -> out.write("Rango mal formado.".getBytes(StandardCharsets.UTF_8)));
        }
        var pieces = ranges.stream().map(r -> new Piece(r.getRangeStart(asset.size),r.getRangeEnd(asset.size))).toList();
        if (pieces.stream().anyMatch(p -> p.start < 0 || p.start >= asset.size || p.end < p.start)) {
            return ResponseEntity.status(416).header(HttpHeaders.CONTENT_RANGE, "bytes */" + asset.size).build();
        }
        if (pieces.size() == 1) {
            var piece = pieces.getFirst();
            headers.set(HttpHeaders.CONTENT_RANGE, piece.range(asset.size));
            headers.setContentLength(piece.length());
            return ResponseEntity.status(206).headers(headers)
                .body((StreamingResponseBody) out -> { try (var input = new RandomAccessFile(file.toFile(),"r")) {
                    copy(input,out,piece);
                }});
        }
        String boundary = UUID.randomUUID().toString();
        var prefixes = pieces.stream().map(p -> ascii("--" + boundary + "\r\nContent-Type: " + asset.mime
            + "\r\nContent-Range: " + p.range(asset.size) + "\r\n\r\n")).toList();
        byte[] ending = ascii("--" + boundary + "--\r\n");
        byte[] newline = ascii("\r\n");
        long length = ending.length;
        for (int i=0;i<pieces.size();i++) length += prefixes.get(i).length + pieces.get(i).length() + newline.length;
        headers.set(HttpHeaders.CONTENT_TYPE,"multipart/byteranges; boundary=" + boundary);
        headers.setContentLength(length);
        return ResponseEntity.status(206).headers(headers).body((StreamingResponseBody) out -> {
            try (var input = new RandomAccessFile(file.toFile(),"r")) {
                for (int i=0;i<pieces.size();i++) {
                    out.write(prefixes.get(i));
                    copy(input,out,pieces.get(i));
                    out.write(newline);
                }
                out.write(ending);
            }
        });
    }

    private static void copy(RandomAccessFile input, OutputStream out, Piece piece) throws IOException {
        input.seek(piece.start);
        byte[] buffer = new byte[16384];
        long remaining = piece.length();
        while (remaining > 0) {
            int count = input.read(buffer,0,(int) Math.min(buffer.length,remaining));
            if (count < 0) throw new EOFException("El medio cambió durante la lectura.");
            out.write(buffer,0,count);
            remaining -= count;
        }
    }

    private static byte[] ascii(String text) { return text.getBytes(StandardCharsets.US_ASCII); }

    private static ApiFailure missing(boolean audio) {
        return new ApiFailure(404, "media_missing", audio ? "El audio de esta canción no está disponible."
            : "No se encuentra esta imagen.");
    }

    private record Asset(String kind,String key,String mime,long size,String sha256) {}
    private record Piece(long start,long end) {
        long length() { return end - start + 1; }
        String range(long total) { return "bytes " + start + "-" + end + "/" + total; }
    }
}
