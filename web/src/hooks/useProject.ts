import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { ProjectInfo } from "../types";

export function useProject() {
  const [data, setData] = useState<ProjectInfo | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api
      .about()
      .then((value) => {
        if (active) setData(value);
      })
      .catch((reason) => {
        if (active) setError(reason.message);
      });
    return () => {
      active = false;
    };
  }, []);
  return { data, error };
}
