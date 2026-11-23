package com.vanipy.tindak;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/**
 * Pure selector shared by the app home screen and the widget. The active view hides
 * finished rows (completed, done, canceled, archived); the history view shows only those.
 * Rows repeated by id are shown once. Section titles from the feed become group headers.
 */
public final class FeedView {
    private FeedView() { }

    /** Group heading row in the app list. */
    public static final class Header {
        public final String title;
        public final int count;
        public Header(String title, int count) { this.title = title; this.count = count; }
    }

    public static boolean isFinished(String status) {
        if (status == null) return false;
        switch (status.trim().toLowerCase(Locale.ROOT)) {
            case "completed": case "complete": case "done": case "canceled": case "cancelled":
            case "archived": case "deleted": case "removed":
                return true;
            default:
                return false;
        }
    }

    /** Flat items only (widget). */
    public static List<FeedParser.Item> items(FeedParser.Feed feed, boolean history) {
        List<FeedParser.Item> out = new ArrayList<>();
        for (Object o : rows(feed, history, false)) if (o instanceof FeedParser.Item) out.add((FeedParser.Item) o);
        return out;
    }

    /** Header objects and FeedParser.Item objects, empty groups dropped. */
    public static List<Object> rows(FeedParser.Feed feed, boolean history, boolean headers) {
        List<Object> out = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        for (FeedParser.Section sec : feed.sections) {
            List<FeedParser.Item> keep = new ArrayList<>();
            for (FeedParser.Item it : sec.items) {
                if (isFinished(it.status) != history) continue;
                if (it.id != null && !it.id.isEmpty() && !seen.add(it.id)) continue;
                keep.add(it);
            }
            if (keep.isEmpty()) continue;
            if (headers && sec.title != null && !sec.title.trim().isEmpty()) out.add(new Header(sec.title.trim(), keep.size()));
            out.addAll(keep);
        }
        return out;
    }
}
