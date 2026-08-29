"use client";

type Props = {
  files: File[];
  onFiles: (files: File[]) => void;
  erpLive?: boolean;
};

const ACCEPT = ".csv,.pdf,.jpg,.jpeg,.png,.webp";

export function Dropzone({ files, onFiles, erpLive = false }: Props) {
  return (
    <section className="relative overflow-hidden rounded-xl bg-card p-5 shadow-lg">
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <h2 className="text-sm font-semibold tracking-wide text-foreground uppercase">Period pack</h2>
        <span className="text-xs text-muted-foreground">CSV · PDF · JPG/PNG/WebP</span>
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
        <p className="text-lg font-semibold text-foreground">Drop this company’s evidence</p>
        <p className="mt-1 text-sm text-muted-foreground">
          UTF-8 ERP CSV plus optional utility PDFs and invoice photos.
          {erpLive ? " Live ERP is connected — files are optional." : " No prompt box."}
        </p>
      </label>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        {files.length === 0 ? (
          <span className="text-xs text-muted-foreground">
            {erpLive ? "No files yet — Run audit will pull live ERP activity." : "At least one file is required to run."}
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
