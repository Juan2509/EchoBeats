package org.echobeats;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.UUID;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Transactional;

import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;

@Service
class WallService {
    private final JdbcTemplate jdbc;
    private final ObjectMapper json;
    private final Path mediaRoot;

    WallService(JdbcTemplate jdbc,ObjectMapper json,@Value("${echobeats.media-root}") String mediaRoot) {
        this.jdbc = jdbc;
        this.json = json;
        this.mediaRoot = Path.of(mediaRoot).toAbsolutePath();
    }

    @Transactional(readOnly=true,isolation=Isolation.REPEATABLE_READ)
    public JsonNode get(UUID albumId) {
        return data(wall(albumId,false).id);
    }

    @Transactional
    public JsonNode replace(UUID albumId,Composition draft,String expected) {
        var target = wall(albumId,true);
        ApiFailure.requireRevision("wall",target.id,target.revision,expected);
        for (var element : draft.elements) {
            if (Boolean.TRUE.equals(jdbc.queryForObject(
                "SELECT EXISTS(SELECT 1 FROM wall_element WHERE id=? AND wall_id<>?)",Boolean.class,element.id,target.id))) {
                throw new ApiFailure(422,"wall_element_conflict","Un elemento pertenece al muro de otro álbum. Usa un ID nuevo.");
            }
        }
        for (var element : draft.elements) validateAsset(element);
        jdbc.update("DELETE FROM wall_element WHERE wall_id=?",target.id);
        var rows = draft.elements.stream().sorted(Comparator.comparing(e -> e.id.toString()))
            .map(e -> new Object[]{e.id,target.id,e.asset,e.kind,e.cx,e.cy,e.width,e.height,e.rotation,e.layer}).toList();
        try {
            if (!rows.isEmpty()) jdbc.batchUpdate("""
                INSERT INTO wall_element(id,wall_id,asset_id,kind,cx,cy,width,height,rotation_deg,z_index)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """, rows);
        } catch (DuplicateKeyException exception) {
            throw new ApiFailure(422,"wall_element_conflict","El ID de un elemento ya está en uso. Recarga el muro antes de guardar.");
        }
        jdbc.update("UPDATE wall SET background_color=?,revision=revision+1,updated_at=now() WHERE id=?",draft.color,target.id);
        return data(target.id);
    }

    private Wall wall(UUID album,boolean lock) {
        var rows = jdbc.query("""
            SELECT a.id AS album_id,w.id,w.revision FROM album a LEFT JOIN wall w ON w.album_id=a.id
            WHERE a.id=?
            """,(r,i) -> new Wall(r.getObject("id",UUID.class),r.getInt("revision")),album);
        if (rows.isEmpty()) throw new ApiFailure(404,"album_not_found","No existe ese álbum.");
        if (rows.getFirst().id != null) {
            if (!lock) return rows.getFirst();
            var locked = jdbc.query("SELECT id,revision FROM wall WHERE album_id=? FOR UPDATE",
                (r,i) -> new Wall(r.getObject("id",UUID.class),r.getInt("revision")),album);
            if (!locked.isEmpty()) return locked.getFirst();
            if (!Boolean.TRUE.equals(jdbc.queryForObject("SELECT EXISTS(SELECT 1 FROM album WHERE id=?)",Boolean.class,album))) {
                throw new ApiFailure(404,"album_not_found","No existe ese álbum.");
            }
        }
        throw new ApiFailure(503,"wall_missing","Falta el muro de este álbum. Comprueba las migraciones.");
    }

    private JsonNode data(UUID wallId) {
        return json.readTree(jdbc.queryForObject("""
            SELECT jsonb_build_object('id',w.id,'album_id',w.album_id,'schema_version',w.schema_version,
                'revision',w.revision,'background_color',w.background_color,'updated_at',w.updated_at,
                'elements',COALESCE((SELECT jsonb_agg(jsonb_build_object(
                    'id',e.id,'asset_id',e.asset_id,'kind',e.kind,'cx',e.cx,'cy',e.cy,'width',e.width,
                    'height',e.height,'rotation_deg',e.rotation_deg,'z_index',e.z_index,
                    'content_url','/api/v1/assets/'||e.asset_id||'/content',
                    'static_preview_url','/api/v1/assets/'||a.static_preview_id||'/content') ORDER BY e.z_index,e.id)
                    FROM wall_element e JOIN media_asset a ON a.id=e.asset_id WHERE e.wall_id=w.id),'[]'::jsonb))
            FROM wall w WHERE w.id=?
            """,String.class,wallId));
    }

    private void validateAsset(Element element) {
        var assets = jdbc.query("""
            SELECT kind,mime_type,frame_count,width_px,height_px,byte_size,storage_key FROM media_asset WHERE id=?
            """,(r,i) -> new Asset(r.getString(1),r.getString(2),r.getInt(3),r.getInt(4),r.getInt(5),
                r.getLong(6),r.getString(7)),element.asset);
        if (assets.isEmpty()) throw new ApiFailure(422,"invalid_wall_asset","Uno de los recursos visuales no existe.");
        var asset = assets.getFirst();
        if (!asset.compatible(element.kind)) throw new ApiFailure(422,"invalid_wall_asset",
            "El recurso no es compatible con este elemento o supera los límites visuales.");
        try {
            Path root = mediaRoot.toRealPath();
            Path candidate = root.resolve(asset.key);
            if (Files.isSymbolicLink(candidate)) throw new IOException();
            Path file = candidate.toRealPath();
            if (file.startsWith(root) && Files.isRegularFile(file) && Files.size(file)==asset.size) return;
        } catch (IOException | IllegalArgumentException ignored) {
            // El resultado es el mismo para una ruta inválida, ausente o inaccesible.
        }
        throw new ApiFailure(422,"wall_asset_missing","No se encuentra uno de los archivos visuales. El muro anterior se conserva.");
    }

    record Composition(String color,List<Element> elements) {
        static Composition initial() { return new Composition("#242038",List.of()); }

        static Composition parse(JsonNode body) {
            var color = body.path("background_color");
            var elements = body.path("elements");
            if (!body.isObject() || body.size()!=3 || !body.path("schema_version").isIntegralNumber()
                || !body.path("schema_version").canConvertToInt() || body.path("schema_version").asInt()!=1
                || !color.isString() || !color.asString().matches("#[0-9a-fA-F]{6}") || !elements.isArray()
                || elements.size()>30) throw invalid();
            var ids = new HashSet<UUID>();
            var values = new ArrayList<Element>();
            for (var node : elements) {
                var element = Element.parse(node);
                if (!ids.add(element.id)) throw invalid();
                values.add(element);
            }
            return new Composition(color.asString().toUpperCase(Locale.ROOT),List.copyOf(values));
        }
    }

    private record Element(UUID id,UUID asset,String kind,double cx,double cy,double width,double height,
                           double rotation,int layer) {
        private static final Set<String> KINDS = Set.of("poster","sticker","image","gif");

        static Element parse(JsonNode node) {
            var layer = node.path("z_index");
            String kind = node.path("kind").asString("");
            if (!node.isObject() || node.size()!=9 || !KINDS.contains(kind) || !layer.isIntegralNumber()
                || !layer.canConvertToInt() || layer.asInt()<0 || layer.asInt()>29) throw invalid();
            double x = number(node,"cx",0,1), y = number(node,"cy",0,1);
            double w = number(node,"width",.03,1), h = number(node,"height",.03,1);
            double raw = number(node,"rotation_deg",-Double.MAX_VALUE,Double.MAX_VALUE);
            double rotation = ((raw + 180) % 360 + 360) % 360 - 180;
            double radians = Math.toRadians(rotation), c = Math.abs(Math.cos(radians)), s = Math.abs(Math.sin(radians));
            double bx = (w*1000*c + h*700*s)/2, by = (w*1000*s + h*700*c)/2, tolerance = 1e-7;
            if (x*1000<bx-tolerance || x*1000>1000-bx+tolerance
                || y*700<by-tolerance || y*700>700-by+tolerance) throw invalid();
            try {
                return new Element(UUID.fromString(node.path("id").asString()),
                    UUID.fromString(node.path("asset_id").asString()),kind,x,y,w,h,rotation,layer.asInt());
            } catch (IllegalArgumentException exception) {
                throw invalid();
            }
        }

        private static double number(JsonNode node,String key,double min,double max) {
            var value = node.path(key);
            double number = value.asDouble(Double.NaN);
            if (!value.isNumber() || !Double.isFinite(number) || number<min || number>max) throw invalid();
            return number;
        }
    }

    private static ApiFailure invalid() {
        return new ApiFailure(422,"invalid_data","Revisa los campos enviados; hay datos vacíos, no válidos o no permitidos.");
    }

    private record Asset(String kind,String mime,int frames,int width,int height,long size,String key) {
        boolean compatible(String element) {
            boolean type = element.equals("gif") ? kind.equals("gif") && mime.equals("image/gif") && frames>=1 && frames<=200
                : Set.of("cover","image").contains(kind) && Set.of("image/png","image/jpeg").contains(mime);
            return type && width>0 && height>0 && width<=4096 && height<=4096 && width*height<=16000000 && size<=5*1024*1024;
        }
    }

    private record Wall(UUID id,int revision) {}
}
