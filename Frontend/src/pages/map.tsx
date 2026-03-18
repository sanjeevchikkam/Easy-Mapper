import { useState } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, AlertCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { UploadZone } from "@/components/UploadZone";
import { StatCard } from "@/components/StatCard";

type AppMode = "pharmacy" | "labtest";
type MappingStats = {
  total: string;
  matched: string;
  unmatched: string;
  threshold: string;
};

function parseStats(firstLine: string): MappingStats {
  const parts = firstLine.replace("#", "").split("|").map((p) => p.trim());
  const find = (key: string) =>
    parts.find((p) => p.startsWith(key))?.split(":")[1]?.trim() || "0";
  return {
    total: find("Total"),
    matched: find("Matched"),
    unmatched: find("Unmatched"),
    threshold: find("Threshold"),
  };
}

export default function Map() {
  const [mode, setMode] = useState<AppMode>("pharmacy");
  const [files, setFiles] = useState<{ inventory: File | null; master: File | null }>({
    inventory: null,
    master: null,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<MappingStats | null>(null);

  const handleFileChange = (type: "inventory" | "master", file: File) => {
    if (file.type === "text/csv" || file.name.endsWith(".csv")) {
      setFiles((prev) => ({ ...prev, [type]: file }));
      setError(null);
    } else {
      setError("Please upload a valid .csv file");
    }
  };

  const handleMatch = async () => {
    if (!files.inventory || !files.master) {
      setError("Please upload both files to proceed.");
      return;
    }

    setLoading(true);
    setError(null);
    setStats(null);

    const formData = new FormData();
    const endpoint = mode === "pharmacy" ? "/pharmacy/pharmacy_match" : "/labtest/labtest_match";

    if (mode === "pharmacy") {
      formData.append("pharmacy_file", files.inventory);
      formData.append("master_file", files.master);
    } else {
      formData.append("lab_file", files.inventory);
      formData.append("master_file", files.master);
    }

    try {
      const response = await fetch(`http://127.0.0.1:8000${endpoint}`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("API mapping failed. Please check file formats.");

      const blob = await response.blob();
      const text = await blob.slice(0, 500).text();
      const firstLine = text.split("\n")[0];

      setStats(parseStats(firstLine));

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `matched_result_${mode}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-svh bg-background">
      {/* Navbar */}
      <nav className="border-b bg-card px-8 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-8">
          <span className="text-xl font-bold tracking-tighter text-primary">
            EASY MAPPER
          </span>
          <Tabs
            value={mode}
            onValueChange={(v) => setMode(v as AppMode)}
            className="w-[400px]"
          >
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="pharmacy">Pharmacy Matching</TabsTrigger>
              <TabsTrigger value="labtest">Lab Test Matching</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto py-12 px-6">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Map mater data with Inventory data.
          </h1>
          <p className="text-sm text-muted mt-1">
            Upload your inventory and master CSV files, then system process and give mapped inventory file.
          </p>
        </div>

        <Card className="shadow-sm overflow-hidden">
          <CardContent className="p-8">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-8">
              <UploadZone
                label="Inventory File"
                file={files.inventory}
                onFileSelect={(f) => handleFileChange("inventory", f)}
              />
              <UploadZone
                label="Master File"
                file={files.master}
                onFileSelect={(f) => handleFileChange("master", f)}
              />
            </div>

            <Button
              onClick={handleMatch}
              disabled={loading}
              className="w-full h-12 text-base font-medium rounded-lg transition-all duration-150"
              size="lg"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Matching in progress...
                </>
              ) : (
                "Match Now"
              )}
            </Button>

            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-6"
                >
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                </motion.div>
              )}
            </AnimatePresence>
          </CardContent>
        </Card>

        <AnimatePresence>
          {stats && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
              className="mt-8 grid grid-cols-2 sm:grid-cols-4 gap-4"
            >
              <StatCard label="Total Records" value={stats.total} />
              <StatCard label="Matched" value={stats.matched} variant="success" />
              <StatCard label="Unmatched" value={stats.unmatched} variant="destructive" />
              <StatCard label="Threshold" value={stats.threshold} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
