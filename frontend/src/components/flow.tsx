import { Label } from "@/components/ui/label";

export function FlowSteps({
  steps,
  current,
}: {
  eyebrow?: string;
  steps: { label: string; body?: string }[];
  current: number;
}) {
  return (
    <ol className="flex flex-wrap items-center gap-y-2 text-sm">
      {steps.map((step, index) => (
        <li key={step.label} className="flex items-center">
          {index > 0 ? <span className="mx-2 h-px w-5 bg-border sm:w-8" aria-hidden /> : null}
          <span
            className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs ${
              index === current
                ? "bg-primary text-primary-foreground"
                : index < current
                  ? "bg-secondary text-secondary-foreground"
                  : "bg-muted text-muted-foreground"
            }`}
          >
            {index + 1}
          </span>
          <span className={`ml-2 ${index === current ? "font-medium" : "text-muted-foreground"}`}>{step.label}</span>
        </li>
      ))}
    </ol>
  );
}

export function Field({
  id,
  label,
  hint,
  children,
}: {
  id: string;
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}
