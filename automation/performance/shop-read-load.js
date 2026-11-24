import http from "k6/http";
import { check, sleep } from "k6";

const apiBaseUrl = (__ENV.SHOPGUARD_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");
const virtualUsers = Number(__ENV.SHOPGUARD_LOAD_VUS || 5);
const testDuration = __ENV.SHOPGUARD_LOAD_DURATION || "30s";
const pauseSeconds = Number(__ENV.SHOPGUARD_LOAD_PAUSE_SECONDS || 1);

export const options = {
  scenarios: {
    shop_read_flow: {
      executor: "constant-vus",
      vus: virtualUsers,
      duration: testDuration,
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<800"],
    checks: ["rate>0.99"],
  },
};

function get(path, name) {
  return http.get(`${apiBaseUrl}${path}`, {
    tags: { name },
    timeout: "5s",
  });
}

export default function () {
  const health = get("/health", "health_check");
  check(health, {
    "health endpoint responds successfully": (response) => response.status === 200,
    "health endpoint reports database ready": (response) =>
      response.json("database") === "ok",
  });

  const products = get("/products", "product_list");
  check(products, {
    "product list responds successfully": (response) => response.status === 200,
    "product list returns a JSON array": (response) => Array.isArray(response.json()),
  });

  const search = get("/products?q=desk", "product_search");
  check(search, {
    "product search responds successfully": (response) => response.status === 200,
    "product search returns a JSON array": (response) => Array.isArray(response.json()),
  });

  sleep(pauseSeconds);
}

export function handleSummary(data) {
  const metrics = data.metrics;
  const valuesFor = (name) => metrics[name].values || metrics[name];
  const requests = valuesFor("http_reqs");
  const failures = valuesFor("http_req_failed");
  const checks = valuesFor("checks");
  const duration = valuesFor("http_req_duration");
  const requestCount = requests.count;
  const failedRate = failures.rate ?? failures.value;
  const checkRate = checks.rate ?? checks.value;
  const p95 = duration["p(95)"];
  const runAt = new Date().toISOString();
  const runStamp = runAt.replace(/[:.]/g, "-");
  const thresholds = {
    request_failures_below_1_percent: failedRate < 0.01,
    p95_below_800_milliseconds: p95 < 800,
    checks_above_99_percent: checkRate > 0.99,
  };
  const report = {
    test_name: "Shop read-only API load check",
    run_at: runAt,
    run_duration_ms: data.state.testRunDurationMs,
    virtual_users: virtualUsers,
    requests: requestCount,
    requests_per_second: requests.rate,
    failed_request_rate: failedRate,
    successful_check_rate: checkRate,
    response_time_ms: {
      average: duration.avg,
      median: duration.med,
      p95,
      maximum: duration.max,
    },
    thresholds,
    passed: Object.values(thresholds).every(Boolean),
  };
  const summary = [
    "\nPhase 9 performance result",
    `Requests: ${report.requests}; failures: ${(failedRate * 100).toFixed(2)}%`,
    `Response time p95: ${p95.toFixed(2)} ms`,
    `Response checks passed: ${(checkRate * 100).toFixed(2)}%`,
    `Thresholds: ${report.passed ? "PASS" : "FAIL"}`,
    "",
  ].join("\n");

  return {
    "outputs/test-results/performance-latest.json": JSON.stringify(report, null, 2),
    [`outputs/test-results/performance-${runStamp}.json`]: JSON.stringify(report, null, 2),
    stdout: summary,
  };
}
