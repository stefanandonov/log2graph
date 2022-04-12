namespace web.Models;

public class Experiment
{
    public int id { get; set; }

    public string name { get; set; }

    public string dataset { get; set; }

    public string windowType { get; set; }

    public long size { get; set; }

    public long slide { get; set; }

    public int? testId { get; set; }

    public bool includeLastEvent { get; set; } = false;

    public Experiment()
    {
        windowType = "tumbling";
        dataset = "NOVA";

    }
}