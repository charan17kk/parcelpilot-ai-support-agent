import { Calculator, Check, Database, FileSearch, Wrench } from "lucide-react";

import type { ToolEvent } from "../types/api";

function toolIcon(name: string) {
  if (name.includes("document")) return FileSearch;
  if (name.includes("calculate")) return Calculator;
  if (name.includes("lookup")) return Database;
  return Wrench;
}

export function ToolTimeline({ events }: { events: ToolEvent[] }) {
  if (!events.length) return null;
  return (
    <details className="tool-timeline">
      <summary>{events.length} tool{events.length === 1 ? "" : "s"} used</summary>
      <div className="tool-list">
        {events.map((event, index) => {
          const Icon = toolIcon(event.tool_name);
          return (
            <div className="tool-row" key={`${event.tool_name}-${index}`}>
              <span className="tool-icon"><Icon size={15} /></span>
              <div>
                <strong>{event.tool_name.replaceAll("_", " ")}</strong>
                <p>{event.output_summary ?? event.input_summary}</p>
              </div>
              <Check className="tool-check" size={15} />
            </div>
          );
        })}
      </div>
    </details>
  );
}
