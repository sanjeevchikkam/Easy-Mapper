import { useRef } from "react";
import { Upload, FileCheck } from "lucide-react";

interface UploadZoneProps {
  label: string;
  file: File | null;
  onFileSelect: (file: File) => void;
}

export function UploadZone({ label, file, onFileSelect }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="space-y-2">
      <label className="text-xs font-medium text-muted uppercase tracking-widest">
        {label}
      </label>
      <div
        onClick={() => inputRef.current?.click()}
        className={`
          h-48 border-2 border-dashed rounded-xl flex flex-col items-center justify-center cursor-pointer
          transition-colors duration-150 group
          ${file ? "border-primary/30 bg-primary/5" : "border-border hover:border-primary/50 hover:bg-accent"}
        `}
      >
        <input
          type="file"
          ref={inputRef}
          className="hidden"
          accept=".csv"
          onChange={(e) => e.target.files?.[0] && onFileSelect(e.target.files[0])}
        />
        {file ? (
          <>
            <FileCheck className="w-10 h-10 text-primary mb-2" />
            <p className="text-sm font-medium text-foreground px-4 text-center truncate w-full">
              {file.name}
            </p>
            <p className="text-xs text-muted mt-1">Click to replace</p>
          </>
        ) : (
          <>
            <Upload className="w-10 h-10 text-border mb-2 group-hover:text-primary/60 transition-colors duration-150" />
            <p className="text-sm text-muted">Drop .csv or click to upload</p>
          </>
        )}
      </div>
    </div>
  );
}
