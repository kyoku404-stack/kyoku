/**
 * KEEP Enterprise Platform — Microservices Operational Status Matrix.
 *
 * Phase: 3.6
 * Role: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import {
  ArrowUpRight,
  Cpu,
  Layers,
  Radio,
  Server,
} from 'lucide-react';
import type { MicroserviceStatusData } from '@/types/system';

interface MicroservicesGridProps {
  services: MicroserviceStatusData[];
  onDeployService?: (serviceName: string) => void;
}

export const MicroservicesGrid: React.FC<MicroservicesGridProps> = ({
  services,
  onDeployService,
}) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Running
          </span>
        );
      case 'STARTING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            Starting
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
            {status}
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur-md mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Server className="w-5 h-5 text-indigo-400" />
            Containerized Microservices Cluster
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Independent autoscalable deployments orchestrated across high-availability availability zones.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 bg-slate-800 rounded-lg text-slate-300 font-medium">
            Active Workloads: {services.length}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {services.map((svc) => (
          <div
            key={svc.service_name}
            className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-4 hover:border-slate-600 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-white truncate" title={svc.service_name}>
                  {svc.service_name}
                </span>
                {getStatusBadge(svc.status)}
              </div>

              <div className="space-y-2 text-xs text-slate-300">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 flex items-center gap-1">
                    <Radio className="w-3.5 h-3.5 text-cyan-400" />
                    Replicas
                  </span>
                  <span className="font-medium text-slate-200">
                    {svc.replicas_ready} / {svc.replicas_desired} Healthy
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-slate-400 flex items-center gap-1">
                    <Cpu className="w-3.5 h-3.5 text-amber-400" />
                    CPU Load
                  </span>
                  <span className="font-medium text-slate-200">{svc.cpu_percent}%</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-slate-400 flex items-center gap-1">
                    <Layers className="w-3.5 h-3.5 text-purple-400" />
                    Memory
                  </span>
                  <span className="font-medium text-slate-200">{svc.memory_mb} MB</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Uptime</span>
                  <span className="font-medium text-slate-200">{svc.uptime_hours} hrs</span>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-700/40 flex items-center justify-between">
              <span className="text-[11px] font-mono text-slate-400">v{svc.version}</span>
              <button
                type="button"
                onClick={() => onDeployService?.(svc.service_name)}
                className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
              >
                Deploy <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
