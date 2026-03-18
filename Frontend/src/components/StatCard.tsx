import { Card, CardContent } from "@/components/ui/card";

interface StatCardProps {
  label: string;
  value: string;
  variant?: "default" | "success" | "destructive";
}

export function StatCard({ label, value, variant = "default" }: StatCardProps) {
  const colorClass =
    variant === "success"
      ? "text-success"
      : variant === "destructive"
        ? "text-destructive"
        : "text-foreground";

  return (
    <Card className="shadow-sm">
      <CardContent className="p-6 flex flex-col items-center justify-center text-center">
        <span className={`text-3xl font-bold tabular-nums tracking-tight ${colorClass}`}>
          {value}
        </span>
        <span className="text-xs font-medium text-muted uppercase tracking-widest mt-1">
          {label}
        </span>
      </CardContent>
    </Card>
  );
}
