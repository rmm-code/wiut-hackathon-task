import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import type { Activity } from "../types";
import { CardHead } from "./Card";
import { Icon } from "./Icon";

export function TrafficSummary({
  onOpen,
  activity,
  roadUsers,
}: {
  activity?: Activity[];
  roadUsers?: number;
  onOpen: () => void;
}) {
  const data = activity ?? [];
  const total =
    roadUsers ??
    data.reduce((sum, item) => sum + item.cars + item.buses + item.people, 0);
  return (
    <section className="card stat-card activity-card">
      <CardHead
        icon="car"
        title="Traffic activity"
        subtitle="Road-user counts"
      />
      <div className="activity-value">
        <strong>{activity ? total : "—"}</strong>
        <span>Tracked road users</span>
      </div>
      {activity ? (
        <>
          <div
            className="activity-chart"
            role="img"
            aria-label="Tracked road users by first appearance"
          >
            <ResponsiveContainer
              width="100%"
              height="100%"
              initialDimension={{ width: 300, height: 110 }}
            >
              <BarChart
                data={data}
                barGap={3}
                margin={{ top: 3, right: 9, bottom: 0, left: 9 }}
              >
                <XAxis
                  dataKey="time"
                  tickFormatter={(value) => value.slice(0, 2) + "m"}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11, fill: "#737373" }}
                  height={21}
                />
                <Tooltip
                  contentStyle={{
                    fontSize: 12,
                    borderRadius: 6,
                    border: "1px solid #e7e7e7",
                  }}
                  cursor={{ fill: "#f7f7f7" }}
                />
                <Bar
                  dataKey="cars"
                  name="Cars"
                  fill="#71a9ed"
                  radius={[3, 3, 0, 0]}
                  maxBarSize={17}
                  isAnimationActive={false}
                />
                <Bar
                  dataKey="buses"
                  name="Large vehicles"
                  fill="#efb366"
                  radius={[3, 3, 0, 0]}
                  maxBarSize={17}
                  isAnimationActive={false}
                />
                <Bar
                  dataKey="people"
                  name="Pedestrians"
                  fill="#73c6a4"
                  radius={[3, 3, 0, 0]}
                  maxBarSize={17}
                  isAnimationActive={false}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="risk-caption activity-legend">
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
      ) : (
        <p className="activity-empty">
          Counts will appear after video analysis.
        </p>
      )}
      <button className="card-footer tinted-green" onClick={onOpen}>
        View samples & insights
        <Icon name="arrow" size={16} />
      </button>
    </section>
  );
}
