import { useEffect, useState } from "react";
import { QualityDashboard } from "./quality-dashboard";
import { Storefront } from "./storefront";

export function App() {
  const [showQuality, setShowQuality] = useState(window.location.hash === "#quality");

  useEffect(() => {
    const updatePage = () => setShowQuality(window.location.hash === "#quality");
    window.addEventListener("hashchange", updatePage);
    return () => window.removeEventListener("hashchange", updatePage);
  }, []);

  useEffect(() => {
    if (!showQuality && window.location.hash.startsWith("#")) {
      const targetId = window.location.hash.slice(1);
      requestAnimationFrame(() => document.getElementById(targetId)?.scrollIntoView());
    }
  }, [showQuality]);

  return showQuality ? <QualityDashboard /> : <Storefront />;
}
