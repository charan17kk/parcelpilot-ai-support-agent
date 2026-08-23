import { AlertTriangle, CheckCircle2, CircleHelp } from "lucide-react";

export function TrustBadge({ confidence }: { confidence: string | null }) {
  if (!confidence) return null;
  const labels = {
    high: { text: "High confidence", Icon: CheckCircle2 },
    medium: { text: "Review advised", Icon: CircleHelp },
    low: { text: "Human review needed", Icon: AlertTriangle },
  } as const;
  const item = labels[confidence as keyof typeof labels] ?? labels.medium;
  return (
    <span className={`trust-badge trust-${confidence}`}>
      <item.Icon size={13} /> {item.text}
    </span>
  );
}
