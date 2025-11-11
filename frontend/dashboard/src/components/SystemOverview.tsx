import React from 'react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';

export function SystemOverview() {
  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-[32px] leading-[40px] font-semibold mb-2">
          Cathay Pacific IROP Re-accommodation System
        </h1>
        <p className="text-[16px] text-muted-foreground">
          Staff Console & IOC Dashboard — Intelligent Operations Recovery Platform
        </p>
      </div>

      <Card className="p-6 rounded-[12px] bg-primary/5 border-primary/20">
        <h2 className="text-[20px] font-semibold mb-3">Design System</h2>
        <div className="space-y-3 text-[14px]">
          <div className="flex items-center gap-3">
            <span className="font-semibold w-32">Primary Color:</span>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded bg-[#006564] border border-border" />
              <span className="font-mono text-[12px]">#006564 Cathay Jade</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-semibold w-32">Accent:</span>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded bg-[#C2262E] border border-border" />
              <span className="font-mono text-[12px]">#C2262E Saffron</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-semibold w-32">Spacing Grid:</span>
            <span>8pt base unit</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-semibold w-32">Card Radius:</span>
            <span>12px</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-semibold w-32">Table Rows:</span>
            <span>44px height</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-semibold w-32">Buttons:</span>
            <span>40px (small) / 48px (large)</span>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-2 gap-6">
        <Card className="p-6 rounded-[12px]">
          <h3 className="text-[18px] leading-[24px] font-semibold mb-3">Components</h3>
          <ul className="space-y-2 text-[14px]">
            <li className="flex items-center gap-2">
              <Badge variant="outline" className="text-[12px]">✓</Badge>
              TopNav with title and actions
            </li>
            <li className="flex items-center gap-2">
              <Badge variant="outline" className="text-[12px]">✓</Badge>
              FilterBar (chips + dropdowns)
            </li>
            <li className="flex items-center gap-2">
              <Badge variant="outline" className="text-[12px]">✓</Badge>
              MetricCard with trends
            </li>
            <li className="flex items-center gap-2">
              <Badge variant="outline" className="text-[12px]">✓</Badge>
              OptionCard (staff variant with WHY accordion)
            </li>
            <li className="flex items-center gap-2">
              <Badge variant="outline" className="text-[12px]">✓</Badge>
              TierTag (Green/Silver/Gold/Diamond)
            </li>
            <li className="flex items-center gap-2">
              <Badge variant="outline" className="text-[12px]">✓</Badge>
              PolicyCallout
            </li>
            <li className="flex items-center gap-2">
              <Badge variant="outline" className="text-[12px]">✓</Badge>
              Sortable, selectable tables
            </li>
            <li className="flex items-center gap-2">
              <Badge variant="outline" className="text-[12px]">✓</Badge>
              Drawer panels
            </li>
            <li className="flex items-center gap-2">
              <Badge variant="outline" className="text-[12px]">✓</Badge>
              Toast notifications
            </li>
          </ul>
        </Card>

        <Card className="p-6 rounded-[12px]">
          <h3 className="text-[18px] leading-[24px] font-semibold mb-3">Views</h3>
          <ul className="space-y-2 text-[14px]">
            <li className="flex items-center gap-2">
              <Badge className="text-[12px]">1</Badge>
              Agent Passenger Panel (3-column)
            </li>
            <li className="flex items-center gap-2">
              <Badge className="text-[12px]">2</Badge>
              IOC Queues Dashboard
            </li>
            <li className="flex items-center gap-2">
              <Badge className="text-[12px]">3</Badge>
              Cohort Detail (split view)
            </li>
            <li className="flex items-center gap-2">
              <Badge className="text-[12px]">4</Badge>
              Reports & Analytics
            </li>
            <li className="flex items-center gap-2">
              <Badge className="text-[12px]">5</Badge>
              State Views (Empty/Loading/Error)
            </li>
          </ul>
        </Card>
      </div>

      <Card className="p-6 rounded-[12px]">
        <h3 className="text-[18px] leading-[24px] font-semibold mb-3">Key Features</h3>
        <div className="grid grid-cols-3 gap-4 text-[14px]">
          <div>
            <h4 className="font-semibold mb-2">Agent Console</h4>
            <ul className="space-y-1 text-muted-foreground">
              <li>• Passenger summary with SSRs</li>
              <li>• Multiple option comparison</li>
              <li>• WHY reasoning for each option</li>
              <li>• TRV score visualization</li>
              <li>• Policy callouts & waivers</li>
              <li>• One-click re-accommodation</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-2">IOC Dashboard</h4>
            <ul className="space-y-1 text-muted-foreground">
              <li>• Real-time metrics</li>
              <li>• Flight queue management</li>
              <li>• Tier/cabin breakdowns</li>
              <li>• Bulk actions</li>
              <li>• Premium inventory protection</li>
              <li>• Exception highlighting</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-2">Analytics</h4>
            <ul className="space-y-1 text-muted-foreground">
              <li>• Auto-reaccommodation trends</li>
              <li>• Time-to-plan distribution</li>
              <li>• Voucher cost tracking</li>
              <li>• Compensation uptake analysis</li>
              <li>• Performance metrics</li>
              <li>• CSV export capability</li>
            </ul>
          </div>
        </div>
      </Card>

      <Card className="p-6 rounded-[12px] bg-success/5 border-success/20">
        <h3 className="text-[18px] leading-[24px] font-semibold mb-3">Interactions</h3>
        <ul className="space-y-2 text-[14px]">
          <li>• Click flight cards in IOC Queue → Navigate to Cohort Detail</li>
          <li>• Select table rows → Open drawer with passenger details</li>
          <li>• Bulk select → Enable batch operations</li>
          <li>• Toggle "Protect premium inventory" → Update option recommendations</li>
          <li>• Click actions → Fire toast confirmations</li>
          <li>• Use top navigation to switch between views</li>
        </ul>
      </Card>
    </div>
  );
}
