import React, { useEffect, useMemo, useState } from 'react';
import { TopNav } from '../components/TopNav';
import { Button } from '../components/ui/button';
import { Checkbox } from '../components/ui/checkbox';
import { Input } from '../components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '../components/ui/sheet';
import { TierTag } from '../components/TierTag';
import { OptionCard } from '../components/OptionCard';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { Pagination, PaginationContent, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious } from '../components/ui/pagination';
import { Search, Download, FileText, AlertTriangle, RefreshCw, Phone, Mail, Users } from 'lucide-react';
import { toast } from 'sonner@2.0.3';
import { Skeleton } from '../components/ui/skeleton';
import { useFlightManifest } from '../hooks/useReaccommodation';

interface CohortDetailProps {
  flightNumber?: string;
  onBack?: () => void;
}

export function CohortDetail({ flightNumber, onBack }: CohortDetailProps) {
  const [selectedPassengers, setSelectedPassengers] = useState<string[]>([]);
  const [selectedPnr, setSelectedPnr] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const { manifest, loading, error, refresh } = useFlightManifest(flightNumber);

  const passengers = manifest?.passengers ?? [];
  const options = manifest?.manifest.options ?? [];
  const crew = manifest?.crew ?? [];
  const disruption = manifest?.disruption;
  const summary = manifest?.manifest.summary;

  useEffect(() => {
    setSelectedPassengers((prev) => prev.filter((pnr) => passengers.some((p) => pnr === p.pnr)));
    if (!passengers.length) {
      setSelectedPnr(null);
      return;
    }
    // Only auto-select if current selection is invalid (not when user explicitly closes)
    if (selectedPnr && !passengers.some((p) => p.pnr === selectedPnr)) {
      setSelectedPnr(passengers[0].pnr);
    }
  }, [passengers, selectedPnr]);

  const filteredPassengers = useMemo(() => {
    if (!searchQuery) return passengers;
    return passengers.filter(
      (p) =>
        p.pnr.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [passengers, searchQuery]);

  const togglePassenger = (pnr: string) => {
    setSelectedPassengers((prev) =>
      prev.includes(pnr) ? prev.filter((p) => p !== pnr) : [...prev, pnr]
    );
  };

  const toggleAll = () => {
    if (selectedPassengers.length === passengers.length) {
      setSelectedPassengers([]);
    } else {
      setSelectedPassengers(passengers.map((p) => p.pnr));
    }
  };

  const handleBulkAccept = () => {
    toast.success(`${selectedPassengers.length} passengers re-accommodated`, {
      description: 'Default options have been ticketed',
    });
    setSelectedPassengers([]);
  };

  const selectedPassenger = passengers.find((p) => p.pnr === selectedPnr) ?? null;
  const recommendedOptionId = selectedPassenger?.defaultOption ?? options[0]?.id;
  const recommendedOption = options.find((option) => option.id === recommendedOptionId) ?? options[0];
  const alternateOptions = options.filter((option) => option.id !== recommendedOption?.id);

  const title = summary ? `Flight ${summary.flightNumber} — ${summary.destination}` : 'Cohort Detail';
  const subtitle = summary
    ? `${summary.route} · ${summary.affectedCount} affected pax · ${summary.statusText}`
    : 'A dynamic cohort built by the orchestration layer';

  return (
    <div className="min-h-screen bg-[#EBEDEC]">
      <TopNav
        title={title}
        subtitle={subtitle}
        actions={
          <div className="flex items-center gap-3">
            {onBack && (
              <Button variant="outline" onClick={onBack}>
                ← Back to Queue
              </Button>
            )}
            <Button variant="outline" onClick={refresh} disabled={loading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh Cohort
            </Button>
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
          </div>
        }
      />

      {error && (
        <div className="px-8 pt-4">
          <div className="p-4 border border-destructive/40 bg-destructive/10 rounded-lg text-sm text-destructive flex items-center justify-between">
            <span>{error}</span>
            <Button variant="outline" size="sm" onClick={refresh}>
              Retry
            </Button>
          </div>
        </div>
      )}

      <div className="flex h-[calc(100vh-64px)]">
        <div className="flex-1 flex flex-col bg-white">
          <div className="p-4 border-b border-border">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search by PNR or name..."
                className="pl-10 h-10"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>

          <div className="flex-1 overflow-auto">
            <Table>
              <TableHeader>
                <TableRow className="h-[44px]">
                  <TableHead className="w-12">
                    <Checkbox
                      checked={passengers.length > 0 && selectedPassengers.length === passengers.length}
                      onCheckedChange={toggleAll}
                      aria-label="Toggle all passengers"
                    />
                  </TableHead>
                  <TableHead>PNR</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Tier</TableHead>
                  <TableHead>Cabin</TableHead>
                  <TableHead>Default Option</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Notes</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading && (
                  <>
                    {Array.from({ length: 6 }).map((_, index) => (
                      <TableRow key={`skeleton-${index}`}>
                        <TableCell colSpan={9}>
                          <Skeleton className="h-6 w-full" />
                        </TableCell>
                      </TableRow>
                    ))}
                  </>
                )}
                {!loading && filteredPassengers.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={9} className="py-10 text-center text-muted-foreground">
                      No passengers match “{searchQuery}”.
                    </TableCell>
                  </TableRow>
                )}
                {!loading &&
                  filteredPassengers.map((passenger) => (
                    <TableRow
                      key={passenger.pnr}
                      className={`h-[44px] cursor-pointer ${
                        selectedPnr === passenger.pnr ? 'bg-primary/5' : ''
                      }`}
                      onClick={() => setSelectedPnr(passenger.pnr)}
                    >
                      <TableCell onClick={(e) => e.stopPropagation()}>
                        <Checkbox
                          checked={selectedPassengers.includes(passenger.pnr)}
                          onCheckedChange={() => togglePassenger(passenger.pnr)}
                          aria-label={`Select passenger ${passenger.pnr}`}
                        />
                      </TableCell>
                      <TableCell className="font-mono text-[12px]">{passenger.pnr}</TableCell>
                      <TableCell className="text-[14px]">{passenger.name}</TableCell>
                      <TableCell>
                        <TierTag tier={passenger.tier} />
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-[12px]">
                          {passenger.cabin}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-[14px] font-semibold">
                        Option {passenger.defaultOption}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 w-16 bg-muted rounded-full overflow-hidden">
                            <div
                              className={`h-full ${
                                passenger.confidence >= 85
                                  ? 'bg-success'
                                  : passenger.confidence >= 70
                                  ? 'bg-warning'
                                  : 'bg-muted-foreground'
                              }`}
                              style={{ width: `${passenger.confidence}%` }}
                            />
                          </div>
                          <span className="text-[12px]">{passenger.confidence}%</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {passenger.hasException ? (
                          <Badge variant="destructive" className="text-[12px] gap-1">
                            <AlertTriangle className="w-3 h-3" />
                            Exception
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-[12px] text-success border-success">
                            Ready
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-[12px] text-muted-foreground">
                        {passenger.notes || '—'}
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </div>

          <div className="h-16 border-t border-border bg-white px-6 flex items-center justify-between">
            {selectedPassengers.length > 0 ? (
              <>
                <span className="text-[14px] text-muted-foreground">
                  {selectedPassengers.length} passenger{selectedPassengers.length !== 1 ? 's' : ''} selected
                </span>
                <div className="flex items-center gap-3">
                  <Button variant="outline" size="sm">
                    <FileText className="w-4 h-4 mr-2" />
                    Add Note
                  </Button>
                  <Button variant="outline" size="sm">
                    Schedule
                  </Button>
                  <Button size="sm" onClick={handleBulkAccept}>
                    Accept Selected
                  </Button>
                </div>
              </>
            ) : (
              <>
                <span className="text-[14px] text-muted-foreground">
                  Showing {filteredPassengers.length} of {passengers.length} passengers
                </span>
                <Pagination>
                  <PaginationContent>
                    <PaginationItem>
                      <PaginationPrevious href="#" />
                    </PaginationItem>
                    <PaginationItem>
                      <PaginationLink href="#" isActive>
                        1
                      </PaginationLink>
                    </PaginationItem>
                    <PaginationItem>
                      <PaginationLink href="#">2</PaginationLink>
                    </PaginationItem>
                    <PaginationItem>
                      <PaginationLink href="#">3</PaginationLink>
                    </PaginationItem>
                    <PaginationItem>
                      <PaginationNext href="#" />
                    </PaginationItem>
                  </PaginationContent>
                </Pagination>
              </>
            )}
          </div>
        </div>

        <Sheet open={!!selectedPassenger} onOpenChange={() => setSelectedPnr(null)}>
          <SheetContent side="right" className="w-[520px] overflow-y-auto">
            {selectedPassenger ? (
              <>
                <SheetHeader>
                  <SheetTitle>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="text-[20px]">{selectedPassenger.name}</span>
                        <TierTag tier={selectedPassenger.tier} />
                      </div>
                      <p className="text-[12px] font-mono text-muted-foreground">
                        PNR: {selectedPassenger.pnr} · Cabin {selectedPassenger.cabin}
                      </p>
                    </div>
                  </SheetTitle>
                  <SheetDescription>
                    Auto-generated plan with crew + passenger context from Mongo/Kafka
                  </SheetDescription>
                </SheetHeader>

                <div className="mt-6 space-y-6">
                  <div className="grid grid-cols-2 gap-3 text-[13px]">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Phone className="w-4 h-4" />
                      <span>{selectedPassenger.contact}</span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Mail className="w-4 h-4" />
                      <span>{selectedPassenger.originalRoute}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-[12px]">
                        SSR: {selectedPassenger.ssrs.length ? selectedPassenger.ssrs.join(', ') : 'None'}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-[12px]">
                        Revenue ${selectedPassenger.value.toLocaleString()}
                      </Badge>
                    </div>
                  </div>

                  {recommendedOption && (
                    <div>
                      <h3 className="text-[14px] font-semibold mb-3">Recommended Option</h3>
                      <OptionCard {...recommendedOption} optionId={recommendedOption.id} selected />
                    </div>
                  )}

                  {alternateOptions.length > 0 && (
                    <>
                      <Separator />
                      <div>
                        <h3 className="text-[14px] font-semibold mb-3">Alternative Options</h3>
                        <div className="space-y-3">
                          {alternateOptions.map((option) => (
                            <OptionCard key={option.id} {...option} optionId={option.id} />
                          ))}
                        </div>
                      </div>
                    </>
                  )}

                  <Separator />

                  <div>
                    <h3 className="text-[14px] font-semibold mb-3">Crew Roster ({crew.length})</h3>
                    <div className="space-y-2">
                      {crew.map((member) => (
                        <div key={member.employeeId} className="flex items-center justify-between border border-border rounded-md px-3 py-2 text-[13px]">
                          <div>
                            <p className="font-semibold">
                              {member.firstName} {member.lastName}
                            </p>
                            <p className="text-muted-foreground text-[12px]">
                              {member.rank} · {member.currentLocation}
                            </p>
                          </div>
                          <Badge variant="outline" className="text-[12px]">
                            {member.assignment?.status ?? 'ON_DUTY'}
                          </Badge>
                        </div>
                      ))}
                      {crew.length === 0 && (
                        <div className="text-muted-foreground text-[12px] border border-dashed rounded-md p-3">
                          Crew data unavailable for this flight.
                        </div>
                      )}
                    </div>
                  </div>

                  {disruption && (
                    <>
                      <Separator />
                      <div>
                        <h3 className="text-[14px] font-semibold mb-3">Disruption Snapshot</h3>
                        <div className="space-y-2 text-[13px]">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-[12px]">
                              {disruption.type}
                            </Badge>
                            <span className="text-muted-foreground">{disruption.status}</span>
                          </div>
                          <div className="text-muted-foreground">
                            Root cause: {disruption.rootCause || 'N/A'}
                          </div>
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Users className="w-4 h-4" />
                            <span>{disruption.passengerImpact?.totalPax} pax impacted · Delay {disruption.impact?.delayMinutes}m</span>
                          </div>
                        </div>
                      </div>
                    </>
                  )}

                  <div>
                    <h3 className="text-[14px] font-semibold mb-3">Actions</h3>
                    <div className="space-y-2">
                      <Button className="w-full h-10">Accept & Ticket</Button>
                      <Button variant="outline" className="w-full h-10">
                        Send Offer to Passenger
                      </Button>
                      <Button variant="outline" className="w-full h-10">
                        Add Note
                      </Button>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground text-sm">
                Select a passenger to inspect options.
              </div>
            )}
          </SheetContent>
        </Sheet>
      </div>
    </div>
  );
}
