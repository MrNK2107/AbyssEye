import React from 'react';
import { CLASS_COLORS } from '@/lib/prototypeData';

export function PageHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {action && <div className="heading-action">{action}</div>}
    </div>
  );
}

export function Panel({
  title,
  icon,
  children,
  className = '',
}: {
  title?: React.ReactNode;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      {title && (
        <div className="panel-title">
          {icon}
          {title}
        </div>
      )}
      {children}
    </section>
  );
}

export function ClassTag({ name }: { name: string }) {
  const colorClass = CLASS_COLORS[name] || '';
  return <span className={`class-tag ${colorClass}`}>{name}</span>;
}

export function StatCard({
  label,
  value,
  icon,
  note,
}: {
  label: string;
  value: React.ReactNode;
  icon: React.ReactNode;
  note?: string;
}) {
  return (
    <div className="stat panel">
      <div className="stat-icon">{icon}</div>
      <div>
        <span className="muted tiny">{label}</span>
        <strong>{value}</strong>
        {note && <small>{note}</small>}
      </div>
    </div>
  );
}
