package org.echobeats;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import tools.jackson.databind.JsonNode;

@Service
class PlaylistService {
    private static final Set<String> FIELDS = Set.of("name","appearance","image_asset_id");
    private final JdbcTemplate jdbc;
    private final NamedParameterJdbcTemplate named;
    private final CatalogReader catalog;

    PlaylistService(JdbcTemplate jdbc,NamedParameterJdbcTemplate named,CatalogReader catalog) {
        this.jdbc=jdbc;
        this.named=named;
        this.catalog=catalog;
    }

    @Transactional
    public JsonNode create(JsonNode body) {
        var fields=parse(body,true);
        requireCover(fields.image);
        var id=UUID.randomUUID();
        jdbc.update("INSERT INTO playlist(id,name,appearance,image_asset_id) VALUES (?,?,?,?)",id,fields.name,
            fields.appearance==null?"vinyl":fields.appearance,fields.image);
        return catalog.playlist(id);
    }

    @Transactional
    public JsonNode edit(UUID id,JsonNode body,String expected) {
        var fields=parse(body,false);
        lock(id,expected);
        if (fields.hasImage) requireCover(fields.image);
        jdbc.update("""
            UPDATE playlist SET name=COALESCE(?,name), appearance=COALESCE(?,appearance),
                image_asset_id=CASE WHEN ? THEN ?::uuid ELSE image_asset_id END,revision=revision+1,updated_at=now()
            WHERE id=?
            """,fields.name,fields.appearance,fields.hasImage,fields.image,id);
        return catalog.playlist(id);
    }

    @Transactional
    public JsonNode tracks(UUID id,JsonNode body,String expected) {
        var values=body.path("track_ids");
        if (!body.isObject() || body.size()!=1 || !values.isArray() || values.size()>1000) throw invalid();
        var ids=new ArrayList<UUID>();
        var distinct=new HashSet<UUID>();
        for (var node : values) {
            var track=parseId(node);
            if (!distinct.add(track)) throw invalid();
            ids.add(track);
        }
        lock(id,expected);
        if (!ids.isEmpty()) {
            long eligible=named.queryForObject("""
                SELECT count(*) FROM track WHERE id IN (:ids) AND deleted_at IS NULL
                """,java.util.Map.of("ids",ids),Long.class);
            if (eligible!=ids.size()) throw new ApiFailure(422,"invalid_tracks",
                "Una de las canciones ya no existe. Recarga la biblioteca.");
        }
        jdbc.update("DELETE FROM playlist_track WHERE playlist_id=?",id);
        var rows=new ArrayList<Object[]>();
        for (int index=0;index<ids.size();index++) rows.add(new Object[]{id,ids.get(index),index});
        if (!rows.isEmpty()) jdbc.batchUpdate("INSERT INTO playlist_track(playlist_id,track_id,position) VALUES (?,?,?)",rows);
        jdbc.update("UPDATE playlist SET revision=revision+1,updated_at=now() WHERE id=?",id);
        return catalog.playlist(id);
    }

    private void lock(UUID id,String expected) {
        List<Integer> revisions=jdbc.queryForList("SELECT revision FROM playlist WHERE id=? FOR UPDATE",Integer.class,id);
        if (revisions.isEmpty()) throw new ApiFailure(404,"playlist_not_found","No existe esa playlist.");
        ApiFailure.requireRevision("playlist",id,revisions.getFirst(),expected);
    }

    private void requireCover(UUID image) {
        if (image != null && !Boolean.TRUE.equals(jdbc.queryForObject("""
            SELECT EXISTS (SELECT 1 FROM media_asset WHERE id=? AND kind IN ('cover','image')
                AND mime_type IN ('image/png','image/jpeg'))
            """,Boolean.class,image))) {
            throw new ApiFailure(422,"invalid_cover","La referencia no corresponde a una portada PNG o JPEG válida.");
        }
    }

    private static Fields parse(JsonNode body,boolean create) {
        if (!body.isObject() || body.properties().stream().anyMatch(field -> !FIELDS.contains(field.getKey()))) throw invalid();
        String name=null,appearance=null;
        if (create || body.has("name")) {
            var node=body.path("name");
            if (!node.isString()) throw invalid();
            name=node.asString().strip();
            if (name.isEmpty() || name.indexOf(0)>=0 || name.codePointCount(0,name.length())>255) throw invalid();
        }
        if (body.has("appearance")) {
            appearance=body.path("appearance").asString("");
            if (!Set.of("vinyl","image").contains(appearance)) throw invalid();
        }
        boolean hasImage=body.has("image_asset_id");
        var value=body.path("image_asset_id");
        UUID image=hasImage && !value.isNull()?parseId(value):null;
        return new Fields(name,appearance,hasImage,image);
    }

    private static UUID parseId(JsonNode node) {
        if (!node.isString()) throw invalid();
        try {
            return UUID.fromString(node.asString());
        } catch (IllegalArgumentException exception) {
            throw invalid();
        }
    }

    private static ApiFailure invalid() {
        return new ApiFailure(422,"invalid_data","Revisa los campos enviados; hay datos vacíos, no válidos o no permitidos.");
    }

    private record Fields(String name,String appearance,boolean hasImage,UUID image) {}
}
