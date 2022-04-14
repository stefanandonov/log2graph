namespace web.Models;

public class Windows
{
    public string type { get; set; }

    public string? error_message { get; set; }
    public List<String> windows { get; set; } = new();

    public string dataset { get; set; } 
}