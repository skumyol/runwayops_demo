export type TierType = 'Green' | 'Silver' | 'Gold' | 'Diamond';

export type SeverityLevel = 'High' | 'Medium' | 'Low';

export interface WhyReason {
  text: string;
  type?: 'tier' | 'time' | 'risk' | 'revenue' | 'policy';
}

export interface ReaccommodationOption {
  id: string;
  departureTime: string;
  arrivalTime: string;
  route: string;
  cabin: string;
  seats: number;
  trvScore: number;
  arrivalDelta?: string | null;
  badges?: ('Greener' | 'Protected' | 'Fastest')[];
  whyReasons: WhyReason[];
}

export interface TierBreakdown {
  tier: TierType;
  count: number;
}

export interface CabinBreakdown {
  cabin: string;
  count: number;
}

export interface CohortPassenger {
  pnr: string;
  name: string;
  tier: TierType;
  defaultOption: string;
  confidence: number;
  hasException: boolean;
  notes?: string;
  cabin: string;
}

export interface FlightSummary {
  flightNumber: string;
  route: string;
  destination: string;
  severity: SeverityLevel;
  affectedCount: number;
  tierBreakdown: TierBreakdown[];
  cabinBreakdown: CabinBreakdown[];
  defaultSuitability: number;
  exceptions: number;
  blockMinutes: number;
  aircraft: string;
  statusText: string;
  updatedAt: string;
}

export interface FlightManifest {
  flightNumber: string;
  summary: FlightSummary;
  passengerIds: string[];
  crewIds: string[];
  options: ReaccommodationOption[];
  cohortPassengers: CohortPassenger[];
  disruptionId?: string | null;
}

export interface PassengerSummary {
  pnr: string;
  name: string;
  tier: TierType;
  cabin: string;
  value: number;
  ssrs: string[];
  contact: string;
  originalFlight: string;
  originalRoute: string;
  originalTime: string;
  isPRM: boolean;
  hasInfant: boolean;
  hasFamily: boolean;
}

export interface PassengerDetail extends PassengerSummary {
  basePassenger: Record<string, unknown>;
  cathayProfile: Record<string, unknown>;
  disruptionContext: Record<string, unknown>;
  metadata: Record<string, unknown>;
}

export interface CrewMember {
  employeeId: string;
  firstName: string;
  lastName: string;
  rank: string;
  base: string;
  currentLocation: string;
  qualifications: Record<string, unknown>;
  duty: Record<string, unknown>;
  assignment?: Record<string, unknown> | null;
  availability: Record<string, unknown>;
  contact: Record<string, unknown>;
  flightNumber: string;
  metadata?: Record<string, unknown>;
}

export interface FlightDisruption {
  disruptionId: string;
  flightNumber: string;
  flightDate: string;
  scheduledDeparture: string;
  scheduledArrival: string;
  type: string;
  rootCause?: string;
  status: string;
  impact: Record<string, unknown>;
  passengerImpact: Record<string, unknown>;
  crewImpact: Record<string, unknown>;
  costEstimate?: Record<string, unknown>;
  actionPlan?: Record<string, unknown>;
  _audit: Record<string, unknown>;
}

export interface FlightQueueResponse {
  flights: FlightSummary[];
}

export interface FlightManifestResponse {
  manifest: FlightManifest;
  passengers: PassengerSummary[];
  crew: CrewMember[];
  disruption?: FlightDisruption | null;
}

export interface PassengerDetailResponse {
  passenger: PassengerDetail;
  flight?: FlightSummary | null;
  options: ReaccommodationOption[];
  crew: CrewMember[];
}
