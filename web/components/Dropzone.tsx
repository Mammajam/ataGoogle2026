"use client";

type Props = {
  files: File[];
  onFiles: (files: File[]) => void;
  usingDemoPack: boolean;
  onUseDemoPack: () => void;
};

const ACCEPT = ".csv,.pdf,.jpg,.jpeg,.png,.webp";

export function Dropzone({ files, onFiles, usingDemoPack, onUseDemoPack }: Props) {
  return (
    <section className="relative overflow-hidden rounded-xl bg-card p-5 shadow-lg">
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <h2 className="text-sm font-semibold tracking-wide text-foreground uppercase">Period pack</h2>
        <span className="text-xs text-muted-foreground">CSV · PDF bill · invoice photo</span>
      </div>
      <label
        className="relative flex min-h-56 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-border bg-input px-4 py-10 text-center transition hover:border-ring"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          onFiles(Array.from(event.dataTransfer.files || []));
        }}
      >
        <input
          type="file"
          accept={ACCEPT}
          multiple
          className="hidden"
          onChange={(event) => onFiles(Array.from(event.target.files || []))}
        />
        <p className="text-lg font-semibold text-foreground">Drop the 2025 evidence pack</p>
        <p className="mt-1 text-sm text-muted-foreground">
          ERP export, electricity bill, diesel receipt. No prompt box.
        </p>
        {usingDemoPack && files.length === 0 ? (
          <span className="pointer-events-none absolute bottom-4 left-4 rounded-lg bg-background px-3 py-2 text-xs font-semibold text-foreground shadow-md">
            Demo pack ready
          </span>
        ) : null}
      </label>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={onUseDemoPack}
          className="rounded-full bg-secondary px-3 py-1.5 text-xs font-semibold text-secondary-foreground transition hover:opacity-90"
        >
          Use demo pack
        </button>
        {usingDemoPack && files.length === 0 ? (
          <span className="text-xs text-muted-foreground">
            erp_export.csv · electricity_bill.pdf · diesel_receipt.jpg
          </span>
        ) : null}
        {files.map((file) => (
          <span
            key={file.name}
            className="rounded-full border border-border bg-background px-2 py-1 text-xs text-foreground"
          >
            {file.name}
          </span>
        ))}
      </div>
    </section>
  );
}
