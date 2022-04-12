namespace web.Models;

public class ExperimentsDto
{
    public int id { get; set; }

    public string name { get; set; }

    public string dataset { get; set; }

    public string window_type { get; set; }

    public long size { get; set; }

    public long slide { get; set; }

    public int? test_id { get; set; }

    public bool include_last_event { get; set; } = false;

    public DateTimeOffset created_at { get; set; }
    
    public DateTimeOffset last_modified_at { get; set; }
    
}