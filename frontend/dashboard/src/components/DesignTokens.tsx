import React from 'react';
import { Card } from './ui/card';
import { TierTag } from './TierTag';
import { TierType } from '../types/reaccommodation';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';

export function DesignTokens() {
  const colors = [
    { name: 'Cathay Jade', hex: '#006564', var: '--cathay-jade' },
    { name: 'White', hex: '#FFFFFF', var: '--cathay-white', border: true },
    { name: 'Medium Jade', hex: '#367D79', var: '--cathay-medium-jade' },
    { name: 'Light Jade', hex: '#5E967E', var: '--cathay-light-jade' },
    { name: 'Sand', hex: '#C1B49A', var: '--cathay-sand' },
    { name: 'Light Sand', hex: '#DCD3BC', var: '--cathay-light-sand' },
    { name: 'Slate', hex: '#C6C2C1', var: '--cathay-slate' },
    { name: 'Light Slate', hex: '#EBEDEC', var: '--cathay-light-slate' },
    { name: 'Saffron (Accent)', hex: '#C2262E', var: '--cathay-saffron' },
  ];

  const semanticColors = [
    { name: 'Success', hex: '#22c55e', var: '--success' },
    { name: 'Warning', hex: '#f59e0b', var: '--warning' },
    { name: 'Info', hex: '#3b82f6', var: '--info' },
  ];

  const tiers: TierType[] = ['Green', 'Silver', 'Gold', 'Diamond'];

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <div>
        <h2 className="text-[24px] leading-[32px] font-semibold mb-2">Design Tokens</h2>
        <p className="text-[14px] text-muted-foreground">
          Cathay Pacific IROP Design System — Color Palette & Components
        </p>
      </div>

      <Card className="p-6 rounded-[12px]">
        <h3 className="text-[18px] leading-[24px] font-semibold mb-4">Primary Colors</h3>
        <div className="grid grid-cols-3 gap-4">
          {colors.map((color) => (
            <div key={color.var} className="flex items-center gap-3">
              <div
                className={`w-12 h-12 rounded-lg ${color.border ? 'border border-border' : ''}`}
                style={{ backgroundColor: color.hex }}
              />
              <div>
                <p className="text-[14px] font-semibold">{color.name}</p>
                <p className="text-[12px] font-mono text-muted-foreground">{color.hex}</p>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card className="p-6 rounded-[12px]">
        <h3 className="text-[18px] leading-[24px] font-semibold mb-4">Semantic Colors</h3>
        <div className="grid grid-cols-3 gap-4">
          {semanticColors.map((color) => (
            <div key={color.var} className="flex items-center gap-3">
              <div
                className="w-12 h-12 rounded-lg"
                style={{ backgroundColor: color.hex }}
              />
              <div>
                <p className="text-[14px] font-semibold">{color.name}</p>
                <p className="text-[12px] font-mono text-muted-foreground">{color.hex}</p>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card className="p-6 rounded-[12px]">
        <h3 className="text-[18px] leading-[24px] font-semibold mb-4">Tier Badges</h3>
        <div className="flex items-center gap-4 flex-wrap">
          {tiers.map((tier) => (
            <TierTag key={tier} tier={tier} />
          ))}
        </div>
      </Card>

      <Card className="p-6 rounded-[12px]">
        <h3 className="text-[18px] leading-[24px] font-semibold mb-4">Typography Scale</h3>
        <div className="space-y-4">
          <div>
            <p className="text-[12px] text-muted-foreground mb-1">Page Title</p>
            <p className="text-[24px] leading-[32px] font-semibold">24px / 32px Semibold</p>
          </div>
          <Separator />
          <div>
            <p className="text-[12px] text-muted-foreground mb-1">Section Title</p>
            <p className="text-[18px] leading-[24px] font-semibold">18px / 24px Semibold</p>
          </div>
          <Separator />
          <div>
            <p className="text-[12px] text-muted-foreground mb-1">Body Text</p>
            <p className="text-[14px] leading-[20px]">14px / 20px Regular</p>
          </div>
          <Separator />
          <div>
            <p className="text-[12px] text-muted-foreground mb-1">Monospace (PNR, Flight Numbers)</p>
            <p className="text-[12px] font-mono">12px Monospace</p>
          </div>
        </div>
      </Card>

      <Card className="p-6 rounded-[12px]">
        <h3 className="text-[18px] leading-[24px] font-semibold mb-4">Spacing & Layout</h3>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <h4 className="text-[14px] font-semibold mb-3">Grid System</h4>
            <ul className="space-y-2 text-[14px]">
              <li className="flex items-center gap-2">
                <Badge variant="outline" className="font-mono text-[12px]">8pt</Badge>
                Base spacing unit
              </li>
              <li className="flex items-center gap-2">
                <Badge variant="outline" className="font-mono text-[12px]">12px</Badge>
                Card border radius
              </li>
              <li className="flex items-center gap-2">
                <Badge variant="outline" className="font-mono text-[12px]">44px</Badge>
                Table row height
              </li>
              <li className="flex items-center gap-2">
                <Badge variant="outline" className="font-mono text-[12px]">40/48px</Badge>
                Button heights
              </li>
            </ul>
          </div>
          <div>
            <h4 className="text-[14px] font-semibold mb-3">Component Sizes</h4>
            <ul className="space-y-2 text-[14px]">
              <li className="flex items-center gap-2">
                <Badge variant="outline" className="font-mono text-[12px]">280px</Badge>
                Sidebar width
              </li>
              <li className="flex items-center gap-2">
                <Badge variant="outline" className="font-mono text-[12px]">320px</Badge>
                Action panel width
              </li>
              <li className="flex items-center gap-2">
                <Badge variant="outline" className="font-mono text-[12px]">480px</Badge>
                Drawer panel width
              </li>
              <li className="flex items-center gap-2">
                <Badge variant="outline" className="font-mono text-[12px]">64px</Badge>
                Top nav height
              </li>
            </ul>
          </div>
        </div>
      </Card>

      <Card className="p-6 rounded-[12px] bg-primary/5 border-primary/20">
        <h3 className="text-[18px] leading-[24px] font-semibold mb-4">Component Library</h3>
        <div className="grid grid-cols-3 gap-3 text-[14px]">
          <div>
            <h4 className="font-semibold mb-2">Navigation</h4>
            <ul className="space-y-1 text-muted-foreground">
              <li>• TopNav</li>
              <li>• FilterBar</li>
              <li>• Tabs</li>
              <li>• Pagination</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-2">Data Display</h4>
            <ul className="space-y-1 text-muted-foreground">
              <li>• MetricCard</li>
              <li>• OptionCard</li>
              <li>• Table</li>
              <li>• Charts (Recharts)</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-2">Feedback</h4>
            <ul className="space-y-1 text-muted-foreground">
              <li>• Toast (Sonner)</li>
              <li>• PolicyCallout</li>
              <li>• Badges</li>
              <li>• State Views</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
}
