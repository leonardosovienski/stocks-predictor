import datetime,hashlib,json,math,pathlib,random,statistics,sys,time
W=pathlib.Path(__file__).parent;sys.path.insert(0,'C:/STOCKS/stocks-predictor/stocks_predictor');import economic_gate
start=time.monotonic();N=504;M=500;allrows=[];summary=[];maxerr=0.;weights_err=0.;v_errors=[];boundary=0
def variance_recursive(phi):
 v=1/(1-phi*phi);cov=0.;vs=0.
 for i in range(N):
  cov=phi*cov
  vs+=v+2*cov
  cov+=v
 return vs/N**2
def bino(k,p):
 pmf=[math.exp(math.lgamma(M+1)-math.lgamma(j+1)-math.lgamma(M-j+1)+j*math.log(p)+(M-j)*math.log1p(-p)) for j in range(M+1)]
 return {'lower_tail':math.fsum(pmf[:k+1]),'two_sided_probability_ordered':math.fsum(q for q in pmf if q<=pmf[k]*(1+1e-10)),'central95_integer_acceptance':[next(j for j in range(M+1) if math.fsum(pmf[:j+1])>=.025),next(j for j in range(M+1) if math.fsum(pmf[:j+1])>=.975)]}
def tcoverage(z,df):
 def f(x):return math.exp(math.lgamma((df+1)/2)-math.lgamma(df/2)-.5*math.log(df*math.pi)-(df+1)/2*math.log1p(x*x/df))
 count=4096;h=z/count
 return 2*h/3*(f(0)+f(z)+4*math.fsum(f(h*i) for i in range(1,count,2))+2*math.fsum(f(h*i) for i in range(2,count,2)))
for phi in [0,.5]:
 v=(N+2*math.fsum((N-k)*phi**k for k in range(1,N)))/(N*N*(1-phi*phi));v_errors.append(abs(v-variance_recursive(phi)));counts=[0,0];changed=[0,0];zvalues=[];means=[];width=[]
 for i in range(M):
  seed=20260911+i;rng=random.Random(seed);x=rng.gauss(0,1/math.sqrt(1-phi*phi));initial=x;innov=[];series=[]
  for t in range(N+200):
   e=rng.gauss(0,1);innov.append(e);x=phi*x+e
   if t>=200:series.append(x)
  # x_t = phi^(t+1)*initial + sum_j<=t phi^(t-j)*e_j.
  # Backward adjoint computes sum of retained x_t without forward AR recurrence.
  adj=0.;terms=[]
  for t in range(N+199,-1,-1):
   adj=(1. if t>=200 else 0.)+phi*adj;terms.append(adj*innov[t])
  weighted=(math.fsum(terms)+phi*adj*initial)/N
  mean=math.fsum(series)/N;weights_err=max(weights_err,abs(mean-weighted))
  sd=math.sqrt(math.fsum((a-mean)**2 for a in series)/(N-1));h=1.96*sd/math.sqrt(N);oracle=1.96*math.sqrt(v)
  est=economic_gate.estimate_edge(series);maxerr=max(maxerr,abs(est.mean_gross_edge-mean),abs(est.lower_gross_edge-(mean-h)))
  hit=[abs(mean)<=h,abs(mean)<=oracle];strict=[abs(mean)<h,abs(mean)<oracle];boundary+=int(hit!=strict)
  for j in range(2):counts[j]+=hit[j]
  changed[0]+=int(hit[1] and not hit[0]);changed[1]+=int(hit[0] and not hit[1]);zvalues.append(mean/math.sqrt(v));means.append(mean);width.append(h/oracle)
  allrows.append({'phi':phi,'seed':seed,'mean':mean,'iid_half_width':h,'oracle_half_width':oracle,'z_oracle':zvalues[-1],'iid_covers':hit[0],'oracle_covers':hit[1]})
  assert time.monotonic()-start<120
 expected_s2=N/(N-1)*(1/(1-phi*phi)-v);ratio=math.sqrt(v/(expected_s2/N))
 summary.append({'phi':phi,'counts':counts,'variance_mean':v,'expected_sample_variance':expected_s2,'oracle_to_iid_se_population_approx':ratio,'known_gamma0_normal_surrogate_coverage':math.erf(1.96/math.sqrt(v*N/(1/(1-phi*phi)))/math.sqrt(2)),'mean_z':statistics.mean(zvalues),'variance_z':statistics.variance(zvalues),'recovered_by_oracle':changed[0],'lost_by_oracle':changed[1],'mean_width_ratio':statistics.mean(width),'oracle_exact_binomial':bino(counts[1],math.erf(1.96/math.sqrt(2))),'iid_exact_null_phi0_only':bino(counts[0],tcoverage(1.96,503)) if phi==0 else None})
a=[r for r in allrows if r['phi']==0];b=[r for r in allrows if r['phi']==.5]
shared=sum(not x['oracle_covers'] and not y['oracle_covers'] for x,y in zip(a,b))
assert [s['counts'] for s in summary]==[[462,464],[359,462]]
assert weights_err<1e-10 and maxerr<1e-12 and max(v_errors)<1e-12 and boundary==0
for s in summary:
 p=s['oracle_exact_binomial']['two_sided_probability_ordered'];s['oracle_exact_binomial']['bonferroni4_p_diagnostic']=min(1,4*p)
 if s['iid_exact_null_phi0_only'] is not None:
  p=s['iid_exact_null_phi0_only']['two_sided_probability_ordered'];s['iid_exact_null_phi0_only']['bonferroni4_p_diagnostic']=min(1,4*p)
receipt={'run_id':'OSS-20260911-01','experiment':'X03','timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protocol_sha256':hashlib.sha256((W/'X03-G1-diagnostic.json').read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'python':sys.version,'summary':summary,'oracle_expected_coverage':math.erf(1.96/math.sqrt(2)),'iid_phi0_expected_student_t503_coverage':tcoverage(1.96,503),'max_production_arithmetic_error':maxerr,'max_independent_weighted_mean_error':weights_err,'variance_recursion_errors':v_errors,'boundary_hit_changes':boundary,'paired_phi_z_correlation':statistics.correlation([r['z_oracle'] for r in a],[r['z_oracle'] for r in b]),'shared_oracle_misses':shared,'closure':'DIAGNOSIS_CLOSED_SCOPE; previous calibration FAIL preserved; no substitute approved','seconds':time.monotonic()-start}
(W/'UNC02-diagnostic-receipt.json').write_text(json.dumps(receipt,indent=2));(W/'UNC02-replay-rows.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in allrows));print(json.dumps(receipt,indent=2))
