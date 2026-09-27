import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CardHead, Empty } from "./Card";
import { Icon } from "./Icon";
import { time } from "../lib/format";
import type { Activity, RiskPoint } from "../types";

const tooltipStyle = {
  border: "1px solid #e9e9ed",
  borderRadius: 9,
  fontSize: 12,
  boxShadow: "0 3px 16px #00000012",
};

export function RiskChart({
  risk,
  position,
}: {
  risk: RiskPoint[];
  position: number;
}) {
  const data = risk.map(([t, value]) => ({
    time: t,
    risk: Math.round(value * 100),
  }));
  const now = [...risk].reverse().find(([t]) => t <= position)?.[1];
  return (
    <section className="card risk-card">
      <CardHead
        icon="chart"
        title="Risk over time"
        subtitle="Accident risk over the next 5 seconds"
        action={
          <span className="subtle-badge">Risk score</span>
        }
      />
      {risk.length ? (
        <>
          <div className="risk-value">
            <strong>
              {now === undefined ? "—" : `${Math.round(now * 100)}%`}
            </strong>
            <span>at {time(position)}</span>
            <span
              className={`badge ${now !== undefined && now >= 0.5 ? "badge-amber" : "badge-green"}`}
            >
              {now !== undefined && now >= 0.5 ? "Elevated" : "Below threshold"}
            </span>
          </div>
          <div
            className="risk-chart"
            role="img"
            aria-label="Risk scores over video time. The alarm threshold is 50 percent."
          >
            <ResponsiveContainer
              width="100%"
              height="100%"
              initialDimension={{ width: 320, height: 180 }}
            >
              <AreaChart
                data={data}
                margin={{ top: 12, right: 15, bottom: 0, left: -25 }}
              >
                <CartesianGrid
                  stroke="#eff0f3"
                  vertical={false}
                  strokeDasharray="3 3"
                />
                <XAxis
                  dataKey="time"
                  type="number"
                  domain={["dataMin", "dataMax"]}
                  tickFormatter={time}
                  tick={{ fontSize: 12, fill: "#8b8c95" }}
                  axisLine={false}
                  tickLine={false}
                  minTickGap={40}
                />
                <YAxis
                  domain={[0, 100]}
                  ticks={[0, 50, 100]}
                  tick={{ fontSize: 12, fill: "#8b8c95" }}
                  tickFormatter={(v) => `${v}%`}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  labelFormatter={(v) => time(Number(v))}
                  formatter={(v) => [`${v}%`, "Risk"]}
                  contentStyle={tooltipStyle}
                />
                <ReferenceLine y={50} stroke="#d8aa5f" strokeDasharray="4 4" />
                <ReferenceLine
                  x={position}
                  stroke="#888888"
                  strokeDasharray="3 3"
                />
                <Area
                  type="monotone"
                  dataKey="risk"
                  stroke="#393939"
                  strokeWidth={2}
                  fill="#eeeeee"
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="risk-caption">
            <span>
              <i className="dot bg-slate" />
              Risk score
            </span>
            <span>
              <i className="threshold-line" />
              Alarm threshold
            </span>
          </div>
        </>
      ) : (
        <Empty
          title="No risk curve yet"
          text="The risk curve appears when the analysis finishes."
          icon="chart"
        />
      )}
      <div className="card-footer">
        <Icon name="info" size={15} />
        <span>Heuristic risk · not a calibrated probability</span>
      </div>
    </section>
  );
}

export function TrafficChart({
  activity,
  source,
}: {
  activity?: Activity[];
  source?: string;
}) {
  return (
    <section className="card">
      <CardHead
        icon="car"
        title="Road users over time"
        subtitle={
          activity
            ? `${source} · tracks by first appearance`
            : "Counts appear when a video's analysis is open"
        }
      />
      {!activity ? (
        <Empty
          title="No counts yet"
          text="Open a sample video to see its road users over time."
          icon="car"
        />
      ) : (
      <>
      <div
        className="traffic-chart"
        role="img"
        aria-label="Measured tracker counts by first appearance"
      >
        <ResponsiveContainer
          width="100%"
          height="100%"
          initialDimension={{ width: 320, height: 180 }}
        >
          <BarChart
            data={activity}
            barGap={4}
            margin={{ left: -25, right: 15, top: 15 }}
          >
            <CartesianGrid vertical={false} stroke="#eff0f3" />
            <XAxis
              dataKey="time"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: "#81828b" }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: "#81828b" }}
            />
            <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#f7f7fa" }} />
            <Bar
              dataKey="cars"
              name="Cars"
              fill="#71a9ed"
              radius={[3, 3, 0, 0]}
              maxBarSize={18}
            />
            <Bar
              dataKey="buses"
              name="Large vehicles"
              fill="#efb366"
              radius={[3, 3, 0, 0]}
              maxBarSize={18}
            />
            <Bar
              dataKey="people"
              name="Pedestrians"
              fill="#73c6a4"
              radius={[3, 3, 0, 0]}
              maxBarSize={18}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="risk-caption chart-legend">
        <span>
          <i className="dot bg-blue" />
          Cars
        </span>
        <span>
          <i className="dot bg-amber" />
          Large vehicles
        </span>
        <span>
          <i className="dot bg-green" />
          Pedestrians
        </span>
      </div>
      </>
      )}
    </section>
  );
}
