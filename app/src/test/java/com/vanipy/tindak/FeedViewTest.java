package com.vanipy.tindak;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import java.util.List;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 32)
public class FeedViewTest {
    private static final String JSON = "{\"generated_at\":\"x\",\"sections\":["
            + "{\"id\":\"a\",\"title\":\"Today\",\"items\":["
            + "{\"id\":\"1\",\"title\":\"Open one\",\"status\":\"\"},"
            + "{\"id\":\"2\",\"title\":\"Fired one-off\",\"status\":\"completed\"},"
            + "{\"id\":\"3\",\"title\":\"Going\",\"status\":\"in_progress\"}]},"
            + "{\"id\":\"b\",\"title\":\"Old\",\"items\":["
            + "{\"id\":\"4\",\"title\":\"Gone\",\"status\":\"Archived\"},"
            + "{\"id\":\"1\",\"title\":\"Open one again\",\"status\":\"\"}]},"
            + "{\"id\":\"c\",\"title\":\"Later\",\"items\":[{\"id\":\"5\",\"title\":\"Dropped\",\"status\":\"canceled\"}]}]}";

    @Test public void activeHidesFinishedAndDuplicates() throws Exception {
        List<Object> rows = FeedView.rows(FeedParser.parse(JSON), false, true);
        assertEquals(3, rows.size()); // header Today, Open one, Going
        assertTrue(rows.get(0) instanceof FeedView.Header);
        assertEquals("Today", ((FeedView.Header) rows.get(0)).title);
        assertEquals(2, ((FeedView.Header) rows.get(0)).count);
        assertEquals("Open one", ((FeedParser.Item) rows.get(1)).title);
    }

    @Test public void historyShowsOnlyFinishedAndDropsEmptyGroups() throws Exception {
        List<Object> rows = FeedView.rows(FeedParser.parse(JSON), true, true);
        assertEquals(6, rows.size()); // Today(1) Old(1) Later(1), each with header
        assertEquals(3, FeedView.items(FeedParser.parse(JSON), true).size());
    }

    @Test public void widgetItemsAreFlatAndActive() throws Exception {
        List<FeedParser.Item> items = FeedView.items(FeedParser.parse(JSON), false);
        assertEquals(2, items.size());
        for (FeedParser.Item it : items) assertFalse(FeedView.isFinished(it.status));
    }

    @Test public void blankStatusIsActive() {
        assertFalse(FeedView.isFinished(""));
        assertFalse(FeedView.isFinished(null));
        assertTrue(FeedView.isFinished(" Completed "));
    }
}
