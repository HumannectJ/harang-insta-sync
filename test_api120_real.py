import json

with open("instagram120_sample.json", "r") as f:
    data = json.load(f)
    print("Type of data:", type(data))
    
    res = data.get("result", {})
    edges = res.get("edges", [])
    
    if len(edges) > 0:
        first_edge = edges[0]
        print("Keys in first edge:", first_edge.keys())
        if "node" in first_edge:
            node = first_edge["node"]
            print("Keys in node:", node.keys())
            print("display_url:", node.get("display_url"))
            print("shortcode:", node.get("shortcode"))
            print("taken_at_timestamp:", node.get("taken_at_timestamp"))
            
            # Caption is usually under edge_media_to_caption -> edges -> node -> text
            caption = ""
            caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
            if len(caption_edges) > 0:
                 caption = caption_edges[0].get("node", {}).get("text", "")
            print("caption:", caption[:50])
