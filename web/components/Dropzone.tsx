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
    <section className="rounded-2xl border border-[#d9d0bf] bg-[#fbf8f1] p-5 shadow-sm">
      <div className="sans mb-3 flex items-baseline justify-between gap-3">
        <h2 className="text-sm font-semibold tracking-wide text-[#1b4d3e] uppercase">
          Period pack
        </h2>
        <span className="text-xs text-[#5c6b62]">CSV · PDF bill · invoice photo</span>
      </div>
      <label
        className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-[#c4a35a]/70 bg-white/60 px-4 py-8 text-center transition hover:border-[#1b4d3e]"
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
        <p className="text-lg text-[#1b4d3e]">Drop the 2025 evidence pack</p>
        <p className="sans mt-1 text-sm text-[#5c6b62]">
          ERP export, electricity bill, diesel receipt. No prompt box.
        </p>
      </label>
      <div className="sans mt-3 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={onUseDemoPack}
          className="rounded-full bg-[#1b4d3e] px-3 py-1.5 text-xs font-semibold text-[#fbf8f1] hover:bg-[#14251c]"
        >
          Use demo pack
        </button>
        {usingDemoPack && files.length === 0 ? (
          <span className="text-xs text-[#2f6f55]">
            erp_export.csv · electricity_bill.pdf · diesel_receipt.jpg
          </span>
        ) : null}
        {files.map((file) => (
          <span
            key={file.name}
            className="rounded-full border border-[#d9d0bf] bg-white px-2 py-1 text-xs text-[#14251c]"
          >
            {file.name}
          </span>
        ))}
      </div>
    </section>
  );
}
