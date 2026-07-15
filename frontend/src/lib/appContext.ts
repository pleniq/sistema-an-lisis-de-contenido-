import { useOutletContext } from "react-router-dom";
import { Dimension, LabelValue, ReelRow } from "./api";

export interface AppContext {
  reels: ReelRow[];
  reloadReels: () => void;
  labelOptions: Record<Dimension, LabelValue[]>;
  reloadLabels: () => void;
  updateReel: (r: ReelRow) => void;
}

export const useApp = () => useOutletContext<AppContext>();
