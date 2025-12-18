package presto.android.gui.clients;

import presto.android.Configs;
import presto.android.Logger;
import presto.android.gui.GUIAnalysisClient;
import presto.android.gui.GUIAnalysisOutput;
import presto.android.gui.graph.NObjectNode;
import presto.android.gui.wtg.EventHandler;
import presto.android.gui.wtg.StackOperation;
import presto.android.gui.wtg.WTGAnalysisOutput;
import presto.android.gui.wtg.WTGBuilder;
import presto.android.gui.wtg.ds.WTG;
import presto.android.gui.wtg.ds.WTGEdge;
import presto.android.gui.wtg.ds.WTGNode;
import soot.SootMethod;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Collection;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/**
 * WTG Visualization Client
 * This client generates a DOT file and an HTML viewer for visualizing the Window Transition Graph
 */
public class WTGVisualizationClient implements GUIAnalysisClient {
    
    @Override
    public void run(GUIAnalysisOutput output) {
        Logger.verb("WTG_VIZ", "=== Starting WTG Visualization ===");
        
        // Build the WTG
        WTGBuilder wtgBuilder = new WTGBuilder();
        wtgBuilder.build(output);
        WTGAnalysisOutput wtgAO = new WTGAnalysisOutput(output, wtgBuilder);
        WTG wtg = wtgAO.getWTG();
        
        // Print WTG statistics
        printWTGStatistics(wtg);
        
        // Generate DOT file
        String dotFile = generateDotFile(wtg);
        
        // Generate HTML viewer
        String htmlFile = generateHTMLViewer(wtg, dotFile);
        
        // Generate JSON summary
        String jsonFile = generateJSONSummary(wtg);
        
        Logger.verb("WTG_VIZ", "=== Visualization Complete ===");
        Logger.verb("WTG_VIZ", "DOT file: " + dotFile);
        Logger.verb("WTG_VIZ", "HTML viewer: " + htmlFile);
        Logger.verb("WTG_VIZ", "JSON summary: " + jsonFile);
        Logger.verb("WTG_VIZ", "");
        Logger.verb("WTG_VIZ", "To view the graph:");
        Logger.verb("WTG_VIZ", "  1. Open " + htmlFile + " in a web browser");
        Logger.verb("WTG_VIZ", "  OR");
        Logger.verb("WTG_VIZ", "  2. Use Graphviz: dot -Tpng " + dotFile + " -o wtg.png");
        Logger.verb("WTG_VIZ", "  3. Use online viewer: https://dreampuf.github.io/GraphvizOnline/");
    }
    
    private void printWTGStatistics(WTG wtg) {
        Collection<WTGEdge> edges = wtg.getEdges();
        Collection<WTGNode> nodes = wtg.getNodes();
        
        Logger.verb("WTG_VIZ", "Application: " + Configs.benchmarkName);
        Logger.verb("WTG_VIZ", "Total Nodes: " + nodes.size());
        Logger.verb("WTG_VIZ", "Total Edges: " + edges.size());
        Logger.verb("WTG_VIZ", "Launcher Node: " + wtg.getLauncherNode());
        Logger.verb("WTG_VIZ", "");
        
        // Print node details
        for (WTGNode n : nodes) {
            Logger.verb("WTG_VIZ", "Node: " + n.getWindow().toString());
            Logger.verb("WTG_VIZ", "  In-edges: " + n.getInEdges().size());
            Logger.verb("WTG_VIZ", "  Out-edges: " + n.getOutEdges().size());
        }
    }
    
    private String generateDotFile(WTG wtg) {
        String dotFilePath = null;
        try {
            // Create output directory structure: output/app_name/
            String baseDir = new File(".").getCanonicalPath();
            // Navigate to project root
            if (baseDir.endsWith("viz-demo")) {
                // AndroidBench/viz-demo -> Gator root
                baseDir = new File(baseDir).getParentFile().getParentFile().getCanonicalPath();
            } else if (baseDir.endsWith("AndroidBench")) {
                // AndroidBench -> Gator root
                baseDir = new File(baseDir).getParentFile().getCanonicalPath();
            } else if (baseDir.contains("AndroidBench")) {
                // AndroidBench/apv or other subdirs -> Gator root
                while (!baseDir.endsWith("Gator") && new File(baseDir).getParentFile() != null) {
                    baseDir = new File(baseDir).getParentFile().getCanonicalPath();
                }
            }
            String outputDir = baseDir + "/output/" + Configs.benchmarkName;
            new File(outputDir).mkdirs();
            
            dotFilePath = outputDir + "/wtg.dot";
            FileWriter output = new FileWriter(dotFilePath);
            BufferedWriter writer = new BufferedWriter(output);
            
            // DOT file header
            writer.write("digraph WTG {\n");
            writer.write("  rankdir=LR;\n");
            writer.write("  node[shape=box, style=rounded, fontname=\"Arial\"];\n");
            writer.write("  edge[fontname=\"Arial\", fontsize=10];\n");
            writer.write("  graph[bgcolor=\"#f5f5f5\", label=\"Window Transition Graph for " + Configs.benchmarkName + "\", labelloc=t, fontsize=16];\n\n");
            
            // Special styling for launcher node
            if (wtg.getLauncherNode() != null) {
                writer.write("  n" + wtg.getLauncherNode().getId() + " [style=\"rounded,filled\", fillcolor=\"#90EE90\", label=\"LAUNCHER\"];\n");
            }
            
            // Draw window nodes
            for (WTGNode wtgNode : wtg.getNodes()) {
                if (wtg.getLauncherNode() != null && wtgNode.getId() == wtg.getLauncherNode().getId()) {
                    continue; // Already handled
                }
                
                String label = escapeLabel(wtgNode.getWindow().toString());
                String simpleName = getSimpleName(label);
                
                writer.write("  n" + wtgNode.getId() + " [label=\"" + simpleName + "\"");
                writer.write(", tooltip=\"" + label + "\"");
                
                // Color code based on type
                if (label.contains("Activity")) {
                    writer.write(", fillcolor=\"#ADD8E6\", style=\"rounded,filled\"");
                } else if (label.contains("Dialog")) {
                    writer.write(", fillcolor=\"#FFB6C1\", style=\"rounded,filled\"");
                }
                writer.write("];\n");
            }
            
            writer.write("\n");
            
            // Draw edges with detailed information
            for (WTGNode wtgNode : wtg.getNodes()) {
                for (WTGEdge edge : wtgNode.getOutEdges()) {
                    WTGNode targetNode = edge.getTargetNode();
                    
                    StringBuilder edgeLabel = new StringBuilder();
                    edgeLabel.append(edge.getEventType() != null ? edge.getEventType().toString() : "event");
                    
                    // Add handler count
                    if (edge.getEventHandlers() != null && !edge.getEventHandlers().isEmpty()) {
                        edgeLabel.append("\\n[").append(edge.getEventHandlers().size()).append(" handlers]");
                    }
                    
                    writer.write("  n" + wtgNode.getId() + " -> n" + targetNode.getId());
                    writer.write(" [label=\"" + escapeLabel(edgeLabel.toString()) + "\"");
                    writer.write(", color=\"#4169E1\"");
                    writer.write("];\n");
                }
            }
            
            writer.write("}\n");
            writer.close();
            
            Logger.verb("WTG_VIZ", "DOT file generated: " + dotFilePath);
            
        } catch (IOException e) {
            e.printStackTrace();
            Logger.err("WTG_VIZ", "Failed to generate DOT file: " + e.getMessage());
        }
        
        return dotFilePath;
    }
    
    private String generateHTMLViewer(WTG wtg, String dotFilePath) {
        String htmlFilePath = null;
        try {
            // Create output directory structure: output/app_name/
            String baseDir = new File(".").getCanonicalPath();
            // Navigate to project root
            if (baseDir.endsWith("viz-demo")) {
                // AndroidBench/viz-demo -> Gator root
                baseDir = new File(baseDir).getParentFile().getParentFile().getCanonicalPath();
            } else if (baseDir.endsWith("AndroidBench")) {
                // AndroidBench -> Gator root
                baseDir = new File(baseDir).getParentFile().getCanonicalPath();
            } else if (baseDir.contains("AndroidBench")) {
                // AndroidBench/apv or other subdirs -> Gator root
                while (!baseDir.endsWith("Gator") && new File(baseDir).getParentFile() != null) {
                    baseDir = new File(baseDir).getParentFile().getCanonicalPath();
                }
            }
            String outputDir = baseDir + "/output/" + Configs.benchmarkName;
            new File(outputDir).mkdirs();
            
            htmlFilePath = outputDir + "/wtg_viewer.html";
            FileWriter output = new FileWriter(htmlFilePath);
            BufferedWriter writer = new BufferedWriter(output);
            
            writer.write("<!DOCTYPE html>\n");
            writer.write("<html>\n");
            writer.write("<head>\n");
            writer.write("  <meta charset=\"UTF-8\">\n");
            writer.write("  <title>WTG Viewer - " + Configs.benchmarkName + "</title>\n");
            writer.write("  <style>\n");
            writer.write("    body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }\n");
            writer.write("    h1 { color: #333; }\n");
            writer.write("    .container { max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }\n");
            writer.write("    .stats { background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }\n");
            writer.write("    .stats-item { display: inline-block; margin: 10px 20px; }\n");
            writer.write("    .stats-label { font-weight: bold; color: #555; }\n");
            writer.write("    .stats-value { color: #2196F3; font-size: 24px; font-weight: bold; }\n");
            writer.write("    .section { margin: 20px 0; }\n");
            writer.write("    .node-list, .edge-list { list-style: none; padding: 0; }\n");
            writer.write("    .node-item, .edge-item { background: #f9f9f9; margin: 5px 0; padding: 10px; border-left: 4px solid #2196F3; }\n");
            writer.write("    .edge-item { border-left-color: #4CAF50; }\n");
            writer.write("    .node-name { font-weight: bold; color: #333; }\n");
            writer.write("    .detail { color: #666; font-size: 14px; margin-left: 20px; }\n");
            writer.write("    .highlight { background: #fff3cd; }\n");
            writer.write("    .dot-section { background: #f8f8f8; padding: 15px; border-radius: 5px; margin: 20px 0; }\n");
            writer.write("    .dot-content { background: #272822; color: #f8f8f2; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: 'Courier New', monospace; font-size: 12px; }\n");
            writer.write("    pre { margin: 0; white-space: pre-wrap; }\n");
            writer.write("    .copy-btn { background: #2196F3; color: white; border: none; padding: 8px 16px; cursor: pointer; border-radius: 4px; margin-top: 10px; }\n");
            writer.write("    .copy-btn:hover { background: #1976D2; }\n");
            writer.write("    .tab-buttons { margin: 20px 0; }\n");
            writer.write("    .tab-btn { background: #e0e0e0; border: none; padding: 10px 20px; cursor: pointer; margin-right: 5px; border-radius: 5px 5px 0 0; }\n");
            writer.write("    .tab-btn.active { background: #2196F3; color: white; }\n");
            writer.write("    .tab-content { display: none; }\n");
            writer.write("    .tab-content.active { display: block; }\n");
            writer.write("  </style>\n");
            writer.write("</head>\n");
            writer.write("<body>\n");
            writer.write("  <div class=\"container\">\n");
            writer.write("    <h1>Window Transition Graph Viewer</h1>\n");
            writer.write("    <h2>" + Configs.benchmarkName + "</h2>\n");
            
            // Statistics section
            writer.write("    <div class=\"stats\">\n");
            writer.write("      <div class=\"stats-item\"><span class=\"stats-label\">Nodes:</span> <span class=\"stats-value\">" + wtg.getNodes().size() + "</span></div>\n");
            writer.write("      <div class=\"stats-item\"><span class=\"stats-label\">Edges:</span> <span class=\"stats-value\">" + wtg.getEdges().size() + "</span></div>\n");
            writer.write("      <div class=\"stats-item\"><span class=\"stats-label\">Launcher:</span> <span class=\"stats-value\">" + (wtg.getLauncherNode() != null ? "Yes" : "No") + "</span></div>\n");
            writer.write("    </div>\n");
            
            // Tabs
            writer.write("    <div class=\"tab-buttons\">\n");
            writer.write("      <button class=\"tab-btn active\" onclick=\"showTab('overview')\">Overview</button>\n");
            writer.write("      <button class=\"tab-btn\" onclick=\"showTab('nodes')\">Nodes</button>\n");
            writer.write("      <button class=\"tab-btn\" onclick=\"showTab('edges')\">Edges</button>\n");
            writer.write("      <button class=\"tab-btn\" onclick=\"showTab('dotfile')\">DOT File</button>\n");
            writer.write("    </div>\n");
            
            // Overview Tab
            writer.write("    <div id=\"overview\" class=\"tab-content active\">\n");
            writer.write("      <h3>How to Visualize</h3>\n");
            writer.write("      <p><strong>Option 1: Online Viewer (Easiest)</strong></p>\n");
            writer.write("      <ol>\n");
            writer.write("        <li>Go to the 'DOT File' tab</li>\n");
            writer.write("        <li>Click 'Copy DOT Content'</li>\n");
            writer.write("        <li>Visit <a href=\"https://dreampuf.github.io/GraphvizOnline/\" target=\"_blank\">https://dreampuf.github.io/GraphvizOnline/</a></li>\n");
            writer.write("        <li>Paste the DOT content</li>\n");
            writer.write("      </ol>\n");
            writer.write("      <p><strong>Option 2: Graphviz Command Line</strong></p>\n");
            writer.write("      <pre>dot -Tpng " + new File(dotFilePath).getName() + " -o wtg.png</pre>\n");
            writer.write("      <p><strong>Option 3: VS Code Extension</strong></p>\n");
            writer.write("      <p>Install 'Graphviz (dot) language support for Visual Studio Code' extension and open the .dot file</p>\n");
            writer.write("    </div>\n");
            
            // Nodes Tab
            writer.write("    <div id=\"nodes\" class=\"tab-content\">\n");
            writer.write("      <h3>WTG Nodes (" + wtg.getNodes().size() + ")</h3>\n");
            writer.write("      <ul class=\"node-list\">\n");
            
            for (WTGNode node : wtg.getNodes()) {
                String nodeName = escapeHTML(node.getWindow().toString());
                boolean isLauncher = wtg.getLauncherNode() != null && node.getId() == wtg.getLauncherNode().getId();
                
                writer.write("        <li class=\"node-item " + (isLauncher ? "highlight" : "") + "\">\n");
                writer.write("          <div class=\"node-name\">Node " + node.getId() + (isLauncher ? " [LAUNCHER]" : "") + "</div>\n");
                writer.write("          <div class=\"detail\">Window: " + nodeName + "</div>\n");
                writer.write("          <div class=\"detail\">In-edges: " + node.getInEdges().size() + ", Out-edges: " + node.getOutEdges().size() + "</div>\n");
                writer.write("        </li>\n");
            }
            
            writer.write("      </ul>\n");
            writer.write("    </div>\n");
            
            // Edges Tab
            writer.write("    <div id=\"edges\" class=\"tab-content\">\n");
            writer.write("      <h3>WTG Edges (" + wtg.getEdges().size() + ")</h3>\n");
            writer.write("      <ul class=\"edge-list\">\n");
            
            int edgeIndex = 1;
            for (WTGEdge edge : wtg.getEdges()) {
                String sourceName = getSimpleName(edge.getSourceNode().getWindow().toString());
                String targetName = getSimpleName(edge.getTargetNode().getWindow().toString());
                String eventType = edge.getEventType() != null ? edge.getEventType().toString() : "Unknown";
                
                writer.write("        <li class=\"edge-item\">\n");
                writer.write("          <div class=\"node-name\">Edge " + edgeIndex + ": " + sourceName + " -&gt; " + targetName + "</div>\n");
                writer.write("          <div class=\"detail\">Event Type: " + eventType + "</div>\n");
                
                if (edge.getEventHandlers() != null && !edge.getEventHandlers().isEmpty()) {
                    writer.write("          <div class=\"detail\">Handlers: " + edge.getEventHandlers().size() + "</div>\n");
                    for (SootMethod handler : edge.getEventHandlers()) {
                        writer.write("          <div class=\"detail\">  * " + escapeHTML(handler.getName()) + "</div>\n");
                    }
                }
                
                if (edge.getCallbacks() != null && !edge.getCallbacks().isEmpty()) {
                    writer.write("          <div class=\"detail\">Callbacks: " + edge.getCallbacks().size() + "</div>\n");
                }
                
                if (edge.getStackOps() != null && !edge.getStackOps().isEmpty()) {
                    writer.write("          <div class=\"detail\">Stack Operations: " + edge.getStackOps().size() + "</div>\n");
                }
                
                writer.write("        </li>\n");
                edgeIndex++;
            }
            
            writer.write("      </ul>\n");
            writer.write("    </div>\n");
            
            // DOT File Tab
            writer.write("    <div id=\"dotfile\" class=\"tab-content\">\n");
            writer.write("      <h3>DOT File Content</h3>\n");
            writer.write("      <p>Copy this content and paste it into <a href=\"https://dreampuf.github.io/GraphvizOnline/\" target=\"_blank\">GraphvizOnline</a></p>\n");
            writer.write("      <button class=\"copy-btn\" onclick=\"copyDotContent()\">Copy DOT Content</button>\n");
            writer.write("      <div class=\"dot-content\">\n");
            writer.write("        <pre id=\"dot-content\">");
            
            // Read and embed DOT file content
            if (dotFilePath != null) {
                try {
                    java.nio.file.Files.lines(new File(dotFilePath).toPath()).forEach(line -> {
                        try {
                            writer.write(escapeHTML(line) + "\n");
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                    });
                } catch (IOException e) {
                    writer.write("Error reading DOT file");
                }
            }
            
            writer.write("</pre>\n");
            writer.write("      </div>\n");
            writer.write("    </div>\n");
            
            // JavaScript
            writer.write("  </div>\n");
            writer.write("  <script>\n");
            writer.write("    function showTab(tabName) {\n");
            writer.write("      var tabs = document.getElementsByClassName('tab-content');\n");
            writer.write("      for (var i = 0; i < tabs.length; i++) {\n");
            writer.write("        tabs[i].classList.remove('active');\n");
            writer.write("      }\n");
            writer.write("      var buttons = document.getElementsByClassName('tab-btn');\n");
            writer.write("      for (var i = 0; i < buttons.length; i++) {\n");
            writer.write("        buttons[i].classList.remove('active');\n");
            writer.write("      }\n");
            writer.write("      document.getElementById(tabName).classList.add('active');\n");
            writer.write("      event.target.classList.add('active');\n");
            writer.write("    }\n");
            writer.write("    \n");
            writer.write("    function copyDotContent() {\n");
            writer.write("      var content = document.getElementById('dot-content').innerText;\n");
            writer.write("      navigator.clipboard.writeText(content).then(function() {\n");
            writer.write("        alert('DOT content copied to clipboard! Now paste it into GraphvizOnline.');\n");
            writer.write("      }, function() {\n");
            writer.write("        alert('Failed to copy. Please select and copy manually.');\n");
            writer.write("      });\n");
            writer.write("    }\n");
            writer.write("  </script>\n");
            writer.write("</body>\n");
            writer.write("</html>\n");
            
            writer.close();
            
            Logger.verb("WTG_VIZ", "HTML viewer generated: " + htmlFilePath);
            
        } catch (IOException e) {
            e.printStackTrace();
            Logger.err("WTG_VIZ", "Failed to generate HTML viewer: " + e.getMessage());
        }
        
        return htmlFilePath;
    }
    
    private String escapeLabel(String label) {
        return label.replace("\"", "\\\"")
                    .replace("\n", "\\n")
                    .replace("\r", "");
    }
    
    private String escapeHTML(String html) {
        return html.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace("\"", "&quot;");
    }
    
    private String getSimpleName(String fullName) {
        // Extract simple class name from full qualified name
        if (fullName.contains(".")) {
            String[] parts = fullName.split("\\.");
            return parts[parts.length - 1];
        }
        return fullName;
    }
    
    private String generateJSONSummary(WTG wtg) {
        String jsonFilePath = null;
        long startTime = System.currentTimeMillis();
        try {
            // Create output directory structure: output/app_name/
            String baseDir = new File(".").getCanonicalPath();
            // Navigate to project root
            if (baseDir.endsWith("viz-demo")) {
                // AndroidBench/viz-demo -> Gator root
                baseDir = new File(baseDir).getParentFile().getParentFile().getCanonicalPath();
            } else if (baseDir.endsWith("AndroidBench")) {
                // AndroidBench -> Gator root
                baseDir = new File(baseDir).getParentFile().getCanonicalPath();
            } else if (baseDir.contains("AndroidBench")) {
                // AndroidBench/apv or other subdirs -> Gator root
                while (!baseDir.endsWith("Gator") && new File(baseDir).getParentFile() != null) {
                    baseDir = new File(baseDir).getParentFile().getCanonicalPath();
                }
            }
            String outputDir = baseDir + "/output/" + Configs.benchmarkName;
            new File(outputDir).mkdirs();
            
            jsonFilePath = outputDir + "/utg.json";
            FileWriter output = new FileWriter(jsonFilePath);
            BufferedWriter writer = new BufferedWriter(output);
            
            // Collect statistics
            Collection<WTGNode> nodes = wtg.getNodes();
            Collection<WTGEdge> edges = wtg.getEdges();
            
            // Count node types
            int activityCount = 0;
            int dialogCount = 0;
            int menuCount = 0;
            int launcherCount = 0;
            
            Set<String> activityNames = new HashSet<>();
            Set<String> dialogNames = new HashSet<>();
            
            for (WTGNode node : nodes) {
                String nodeName = node.getWindow().toString();
                if (nodeName.contains("LAUNCHER")) {
                    launcherCount++;
                } else if (nodeName.contains("ACT[")) {
                    activityCount++;
                    // Extract activity class name
                    if (nodeName.contains("[") && nodeName.contains("]")) {
                        String className = nodeName.substring(nodeName.indexOf("[") + 1, nodeName.lastIndexOf("]"));
                        activityNames.add(className);
                    }
                } else if (nodeName.contains("DIALOG[")) {
                    dialogCount++;
                    if (nodeName.contains("[") && nodeName.indexOf("]") > 0) {
                        String className = nodeName.substring(nodeName.indexOf("[") + 1, nodeName.indexOf("]"));
                        dialogNames.add(className);
                    }
                } else if (nodeName.contains("Menu")) {
                    menuCount++;
                }
            }
            
            // Count edge types
            Map<String, Integer> eventTypeCounts = new HashMap<>();
            int totalHandlers = 0;
            int totalCallbacks = 0;
            
            for (WTGEdge edge : edges) {
                String eventType = edge.getEventType() != null ? edge.getEventType().toString() : "unknown";
                eventTypeCounts.put(eventType, eventTypeCounts.getOrDefault(eventType, 0) + 1);
                
                if (edge.getEventHandlers() != null) {
                    totalHandlers += edge.getEventHandlers().size();
                }
                if (edge.getCallbacks() != null) {
                    totalCallbacks += edge.getCallbacks().size();
                }
            }
            
            // Calculate analysis duration
            long endTime = System.currentTimeMillis();
            double durationSeconds = (endTime - startTime) / 1000.0;
            
            // Build JSON
            writer.write("{\n");
            writer.write("  \"application\": \"" + escapeJSON(Configs.benchmarkName) + "\",\n");
            writer.write("  \"analysis_time\": \"" + new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date()) + "\",\n");
            writer.write("  \"analysis_duration_seconds\": " + String.format("%.3f", durationSeconds) + ",\n");
            writer.write("  \"summary\": {\n");
            writer.write("    \"total_nodes\": " + nodes.size() + ",\n");
            writer.write("    \"total_edges\": " + edges.size() + ",\n");
            writer.write("    \"launcher_nodes\": " + launcherCount + ",\n");
            writer.write("    \"activity_nodes\": " + activityCount + ",\n");
            writer.write("    \"dialog_nodes\": " + dialogCount + ",\n");
            writer.write("    \"menu_nodes\": " + menuCount + ",\n");
            writer.write("    \"total_event_handlers\": " + totalHandlers + ",\n");
            writer.write("    \"total_callbacks\": " + totalCallbacks + "\n");
            writer.write("  },\n");
            
            // Activities
            writer.write("  \"activities\": [\n");
            int count = 0;
            for (String activity : activityNames) {
                writer.write("    \"" + escapeJSON(activity) + "\"");
                if (++count < activityNames.size()) writer.write(",");
                writer.write("\n");
            }
            writer.write("  ],\n");
            
            // Dialogs
            writer.write("  \"dialogs\": [\n");
            count = 0;
            for (String dialog : dialogNames) {
                writer.write("    \"" + escapeJSON(dialog) + "\"");
                if (++count < dialogNames.size()) writer.write(",");
                writer.write("\n");
            }
            writer.write("  ],\n");
            
            // Event types
            writer.write("  \"event_types\": {\n");
            count = 0;
            for (Map.Entry<String, Integer> entry : eventTypeCounts.entrySet()) {
                writer.write("    \"" + escapeJSON(entry.getKey()) + "\": " + entry.getValue());
                if (++count < eventTypeCounts.size()) writer.write(",");
                writer.write("\n");
            }
            writer.write("  },\n");
            
            // Node details
            writer.write("  \"nodes\": [\n");
            count = 0;
            for (WTGNode node : nodes) {
                writer.write("    {\n");
                writer.write("      \"id\": " + node.getId() + ",\n");
                writer.write("      \"type\": \"" + escapeJSON(getNodeType(node)) + "\",\n");
                writer.write("      \"window\": \"" + escapeJSON(node.getWindow().toString()) + "\",\n");
                writer.write("      \"in_edges\": " + node.getInEdges().size() + ",\n");
                writer.write("      \"out_edges\": " + node.getOutEdges().size() + "\n");
                writer.write("    }");
                if (++count < nodes.size()) writer.write(",");
                writer.write("\n");
            }
            writer.write("  ],\n");
            
            // Edge details
            writer.write("  \"edges\": [\n");
            count = 0;
            for (WTGEdge edge : edges) {
                writer.write("    {\n");
                writer.write("      \"source_id\": " + edge.getSourceNode().getId() + ",\n");
                writer.write("      \"target_id\": " + edge.getTargetNode().getId() + ",\n");
                writer.write("      \"event_type\": \"" + escapeJSON(edge.getEventType() != null ? edge.getEventType().toString() : "unknown") + "\",\n");
                writer.write("      \"handlers\": " + (edge.getEventHandlers() != null ? edge.getEventHandlers().size() : 0) + ",\n");
                writer.write("      \"callbacks\": " + (edge.getCallbacks() != null ? edge.getCallbacks().size() : 0) + "\n");
                writer.write("    }");
                if (++count < edges.size()) writer.write(",");
                writer.write("\n");
            }
            writer.write("  ]\n");
            
            writer.write("}\n");
            writer.close();
            
            Logger.verb("WTG_VIZ", "UTG JSON generated: " + jsonFilePath);
            
        } catch (IOException e) {
            e.printStackTrace();
            Logger.err("WTG_VIZ", "Failed to generate JSON summary: " + e.getMessage());
        }
        
        return jsonFilePath;
    }
    
    private String getNodeType(WTGNode node) {
        String nodeName = node.getWindow().toString();
        if (nodeName.contains("LAUNCHER")) {
            return "Launcher";
        } else if (nodeName.contains("ACT[")) {
            return "Activity";
        } else if (nodeName.contains("DIALOG[")) {
            return "Dialog";
        } else if (nodeName.contains("OptionsMenu")) {
            return "OptionsMenu";
        } else if (nodeName.contains("ContextMenu")) {
            return "ContextMenu";
        }
        return "Other";
    }
    
    private String escapeJSON(String str) {
        if (str == null) return "";
        return str.replace("\\", "\\\\")
                  .replace("\"", "\\\"")
                  .replace("\n", "\\n")
                  .replace("\r", "\\r")
                  .replace("\t", "\\t");
    }
}
