"""Generate documented PBIP/PBIR plus TMSL semantic model. Native Desktop acceptance pending."""
from pathlib import Path
import json, uuid
import pandas as pd
from data_processing import ROOT

PBI=ROOT/'powerbi';REPORT=PBI/'SaaS.Report';MODEL=PBI/'SaaS.SemanticModel'
SCHEMA='https://developer.microsoft.com/json-schemas/fabric/'
def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,indent=2,ensure_ascii=False))
def literal(value):
    v=('true' if value else 'false') if isinstance(value,bool) else (f"'{value}'" if isinstance(value,str) else f'{value}D')
    return {'expr':{'Literal':{'Value':v}}}
def field(table,column,measure=False):
    return {('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':column}}
def projection(t,c,measure=False):
    return {'field':field(t,c,measure),'queryRef':f'{t}.{c}','nativeQueryRef':c}

MEASURES={
 'Active Customers':("VAR d = MAX(FactMonthlySnapshot[month_end]) RETURN CALCULATE(SUM(FactMonthlySnapshot[active_customers]), KEEPFILTERS(FactMonthlySnapshot[month_end] = d))",'#,0'),
 'Beginning Customers':("SUM(FactMonthlySnapshot[beginning_customers])",'#,0'),
 'New Customers':("SUM(FactMonthlySnapshot[new_customers])",'#,0'),
 'Churned Customers':("SUM(FactMonthlySnapshot[churned_customers])",'#,0'),
 'Customer Churn Rate':("DIVIDE([Churned Customers], [Beginning Customers])",'0.00%'),
 'Customer Retention Rate':("IF(NOT ISBLANK([Customer Churn Rate]), 1 - [Customer Churn Rate])",'0.00%'),
 'MRR':("VAR d = MAX(FactMonthlySnapshot[month_end]) RETURN CALCULATE(SUM(FactMonthlySnapshot[active_mrr]), KEEPFILTERS(FactMonthlySnapshot[month_end] = d))",'"CU "#,0'),
 'ARR':("[MRR] * 12",'"CU "#,0'),
 'Beginning MRR':("SUM(FactMonthlySnapshot[beginning_mrr])",'"CU "#,0'),
 'Churned MRR':("SUM(FactMonthlySnapshot[churned_mrr])",'"CU "#,0'),
 'Gross Revenue Churn':("DIVIDE([Churned MRR], [Beginning MRR])",'0.00%'),
 'Gross Revenue Retention':("IF(NOT ISBLANK([Gross Revenue Churn]), 1 - [Gross Revenue Churn])",'0.00%'),
 'ARPA':("DIVIDE([MRR], [Active Customers])",'"CU "#,0.00'),
 'Average Churn Tenure Days':("DIVIDE(SUM(FactMonthlySnapshot[churned_tenure_days]), [Churned Customers])",'0'),
 'Payment Attempts':("COUNTROWS(FactPayment)",'#,0'),
 'Failed Payments':("CALCULATE(COUNTROWS(FactPayment), FactPayment[payment_status] = \"failed\")",'#,0'),
 'Succeeded Payments':("CALCULATE(COUNTROWS(FactPayment), FactPayment[payment_status] = \"succeeded\")",'#,0'),
 'Failed Payment Rate':("DIVIDE([Failed Payments], [Payment Attempts])",'0.00%'),
 'Accounts With Failed Payments':("CALCULATE(DISTINCTCOUNT(FactPayment[account_id]), FactPayment[payment_status] = \"failed\")",'#,0'),
 'Invoiced Value':("SUM(FactInvoice[amount_due])",'"CU "#,0'),
 'Collected Value':("CALCULATE(SUM(FactPayment[amount]), FactPayment[payment_status] = \"succeeded\")",'"CU "#,0'),
 'Open Invoice Value':("CALCULATE(SUM(FactInvoice[amount_due]), FactInvoice[invoice_status] = \"open\")",'"CU "#,0'),
 'MRR at Risk':("VAR d = MAX(FactMonthlySnapshot[month_end]) RETURN CALCULATE(SUM(FactMonthlySnapshot[mrr_at_risk]), KEEPFILTERS(FactMonthlySnapshot[month_end] = d))",'"CU "#,0'),
 'Risk Accounts':("VAR d = MAX(FactMonthlySnapshot[month_end]) RETURN CALCULATE(SUM(FactMonthlySnapshot[risk_accounts]), KEEPFILTERS(FactMonthlySnapshot[month_end] = d))",'#,0'),
 'Cohort Retention':("DIVIDE(SUM(FactCohort[retained]), SUM(FactCohort[cohort_accounts]))",'0.0%'),
 'Landmark Churn 90d':("DIVIDE(SUM(FactLandmark[churn_next90]), COUNTROWS(FactLandmark))",'0.00%'),
 'Landmark Accounts':("COUNTROWS(FactLandmark)",'#,0'),
 'Latest Priority MRR':("CALCULATE(SUM(FactRisk[mrr]), FactRisk[risk_flag] = 1)",'"CU "#,0'),
 'Priority Failed Attempts':("IF(NOT ISBLANK([Latest Priority MRR]), SUM(FactRisk[failed_30d]))",'#,0'),
 'Priority Mature Balance':("IF(NOT ISBLANK([Latest Priority MRR]), SUM(FactRisk[overdue_value]))",'"CU "#,0'),
}

def table(name,path,include=None):
    df=pd.read_csv(ROOT/path,keep_default_na=False)
    if include:df=df[include]
    cols=[];types=[]
    for col in df:
        date=col.endswith('_at') or col.endswith('_date') or col in ['date','cohort','landmark','month_start','month_end']
        dtype='dateTime' if date else ('int64' if pd.api.types.is_integer_dtype(df[col]) else ('double' if pd.api.types.is_numeric_dtype(df[col]) else 'string'))
        cols.append({'name':col,'dataType':dtype,'sourceColumn':col,'summarizeBy':'none'})
        typ={'dateTime':'type date','int64':'Int64.Type','double':'type number','string':'type text'}[dtype]
        types.append('{"'+col+'", '+typ+'}')
    expr=['let',f'    Source = Csv.Document(' + (f'Binary.Decompress(File.Contents(ProjectRoot & "/{path}"), Compression.GZip)' if path.endswith('.gz') else f'File.Contents(ProjectRoot & "/{path}")') + ', [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),', '    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),']
    if include:expr+=['    Selected = Table.SelectColumns(Headers, {'+', '.join('"'+x+'"' for x in include)+'}),'];base='Selected'
    else:base='Headers'
    expr += [f'    BlankDates = Table.ReplaceValue({base}, "", null, Replacer.ReplaceValue, {{'+', '.join('"'+x['name']+'"' for x in cols if x['dataType']=='dateTime')+'}),', '    Typed = Table.TransformColumnTypes(BlankDates, {'+', '.join(types)+'}, "en-US")','in','    Typed']
    if name=='DimDate':
        for c in cols:
            if c['name']=='month_year':c['sortByColumn']='year_month_sort'
            if c['name']=='month':c['sortByColumn']='month_number'
            if c['name']=='date':c['isKey']=True
    return {'name':name,'columns':cols,'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':expr}}]}

def build():
    tables=[table('DimAccount','data/raw/accounts.csv'),table('DimPlan','data/raw/plans.csv'),table('DimDate','data/processed/dim_date.csv'),table('FactSubscription','data/processed/customer_analytics.csv',['subscription_id','account_id','plan_id','started_at','ended_at','mrr','seats','tenure_days','tenure_bucket']),table('FactMonthlySnapshot','data/processed/subscription_monthly_snapshot.csv.gz'),table('FactInvoice','data/processed/fact_invoice.csv'),table('FactPayment','data/processed/fact_payment.csv'),table('FactCohort','data/processed/fact_cohort.csv'),table('FactRisk','data/processed/billing_risk_accounts.csv',['account_id','plan_id','mrr','risk_flag','risk_group','failed_30d','overdue_value','overdue_invoices','retried_invoices_30d']),table('FactLandmark','data/processed/landmark_features.csv',['account_id','plan_id','landmark','risk_group','failed_30d','overdue_invoices','tenure_at_landmark','churn_next90'])]
    tables[3]['measures']=[{'name':n,'expression':e,'formatString':fmt,'displayFolder':'SaaS KPIs','description':'See docs/metric_definitions.md; source classification is synthetic.'} for n,(e,fmt) in MEASURES.items()]
    relations=[]
    for t in tables[3:]:
        for dim,key in [('DimAccount','account_id'),('DimPlan','plan_id')]:
            relations.append({'name':t['name']+'_'+dim,'fromTable':t['name'],'fromColumn':key,'toTable':dim,'toColumn':key,'crossFilteringBehavior':'oneDirection','fromCardinality':'many','toCardinality':'one'})
    for fact,col in [('FactMonthlySnapshot','month_end'),('FactInvoice','invoice_date'),('FactPayment','attempted_at')]:
        relations.append({'name':fact+'_DimDate','fromTable':fact,'fromColumn':col,'toTable':'DimDate','toColumn':'date','crossFilteringBehavior':'oneDirection','fromCardinality':'many','toCardinality':'one'})
    model={'name':'SaaS Revenue Intelligence','compatibilityLevel':1600,'model':{'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','sourceQueryCulture':'en-US','expressions':[{'name':'ProjectRoot','kind':'m','expression':'"C:/CHANGE_ME/churnanalysis" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}],'tables':tables,'relationships':relations,'annotations':[{'name':'PBI_QueryOrder','value':json.dumps(['ProjectRoot']+[t['name'] for t in tables])},{'name':'PBI_TimeIntelligenceEnabled','value':'0'}]}}
    write(MODEL/'model.bim',model)
    write(MODEL/'definition.pbism',{'version':'1.0','settings':{}})
    write(PBI/'SaaS_Churn_Revenue_Intelligence.pbip',{'$schema':SCHEMA+'pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':'SaaS.Report'}}],'settings':{'enableAutoRecovery':True}})
    write(REPORT/'definition.pbir',{'$schema':SCHEMA+'item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../SaaS.SemanticModel'}}})
    definition=REPORT/'definition'
    write(definition/'version.json',{'$schema':SCHEMA+'item/report/definition/versionMetadata/1.0.0/schema.json','version':'2.0.0'})
    write(definition/'report.json',{'$schema':SCHEMA+'item/report/definition/report/1.0.0/schema.json','layoutOptimization':'None','themeCollection':{'baseTheme':{'name':'CY24SU02','reportVersionAtImport':'5.55','type':'SharedResources'}}})
    pages=[]
    def page(name,title):
        pages.append(name);folder=definition/'pages'/name
        write(folder/'page.json',{'$schema':SCHEMA+'item/report/definition/page/1.0.0/schema.json','name':name,'displayName':title,'displayOption':'FitToPage','width':1600,'height':1000,'objects':{'background':[{'properties':{'color':{'solid':{'color':literal('#F2F5F8')}},'transparency':literal(0)}}]}})
        return folder
    def visual(folder,name,vtype,roles,pos,title=None):
        x,y,w,h=pos
        q={role:{'projections':[projection(*f) for f in fields]} for role,fields in roles.items()}
        vc={'$schema':SCHEMA+'item/report/definition/visualContainer/2.1.0/schema.json','name':name,'position':{'x':x,'y':y,'z':0,'width':w,'height':h,'tabOrder':0},'visual':{'visualType':vtype,'query':{'queryState':q},'drillFilterOtherVisuals':True,'visualContainerObjects':{'background':[{'properties':{'show':literal(True),'color':{'solid':{'color':literal('#FFFFFF')}},'transparency':literal(0)}}]}}}
        if title:vc['visual']['visualContainerObjects']['title']=[{'properties':{'show':literal(True),'text':literal(title),'fontSize':literal(13),'fontColor':{'solid':{'color':literal('#13253C')}}}}]
        write(folder/'visuals'/name/'visual.json',vc)
    def slicers(folder):
        for j,(t,c,title) in enumerate([('DimDate','month_year','Month'),('DimPlan','plan_name','Plan'),('DimAccount','segment','Segment'),('DimAccount','region','Region'),('DimAccount','acquisition_channel','Channel')]):
            visual(folder,'slicer'+str(j),'slicer',{'Values':[(t,c,False)]},(35+j*310,20,295,90),title)
    def cards(folder,names):
        w=1530/len(names)
        for j,n in enumerate(names):visual(folder,'kpi'+str(j),'card',{'Values':[('FactSubscription',n,True)]},(35+j*w,130,w-15,95),n)
    def line(folder,name,measures,pos,title):
        visual(folder,name,'lineChart',{'Category':[('DimDate','month_end',False)],'Y':[('FactSubscription',n,True) for n in measures]},pos,title)
        path=folder/'visuals'/name/'visual.json'
        obj=json.loads(path.read_text());obj['visual']['query']['sortDefinition']={'sort':[{'field':field('DimDate','month_end'),'direction':'Ascending'}],'isDefaultSort':True}
        write(path,obj)
    def bar(folder,name,t,c,n,pos,title):visual(folder,name,'barChart',{'Category':[(t,c,False)],'Y':[('FactSubscription',n,True)]},pos,title)
    a=page('Executive','Executive SaaS Overview');slicers(a)
    cards(a,['Active Customers','MRR','ARR','Customer Churn Rate','Gross Revenue Churn','Gross Revenue Retention','Churned MRR','ARPA'])
    line(a,'mrr',['MRR'],(35,255,990,330),'Monthly active MRR · CU')
    bar(a,'mix','DimPlan','plan_name','MRR',(1045,255,515,330),'MRR by plan · latest selected month')
    line(a,'movement',['New Customers','Churned Customers'],(35,610,490,330),'Monthly customer movement')
    line(a,'churn',['Customer Churn Rate'],(545,610,490,330),'Monthly logo churn')
    line(a,'loss',['Churned MRR'],(1055,610,505,330),'Monthly cancellation MRR · CU')
    b=page('Retention','Customer Retention Intelligence');slicers(b)
    cards(b,['Churned Customers','Customer Retention Rate','Average Churn Tenure Days','Churned MRR'])
    visual(b,'cohorts','pivotTable',{'Rows':[('FactCohort','cohort',False)],'Columns':[('FactCohort','age_months',False)],'Values':[('FactSubscription','Cohort Retention',True)]},(35,255,850,425),'Cohort retention · observed month-end ages; date slicer does not filter cohorts')
    for j,(t,c,title) in enumerate([('DimPlan','plan_name','Churn by plan'),('DimAccount','segment','Churn by segment'),('DimAccount','acquisition_channel','Churn by channel'),('DimAccount','region','Churn by region')]):
        bar(b,'breakdown'+str(j),t,c,'Customer Churn Rate',(905+(j%2)*335,255+(j//2)*220,315,200),title)
    visual(b,'highvalue','tableEx',{'Values':[('DimAccount','account_id',False),('DimPlan','plan_name',False),('FactSubscription','Churned MRR',True),('FactSubscription','Average Churn Tenure Days',True)]},(35,705,850,250),'Cancellation accounts · select month/dimensions; sort Churned MRR descending')
    # Tenure linked through account identity; explicit cancellation measure uses subscription end dates.
    tables[3]['measures'].append({'name':'Tenure Cancellations','expression':'VAR Dates = VALUES(DimDate[date]) RETURN CALCULATE(COUNTROWS(FactSubscription), TREATAS(Dates, FactSubscription[ended_at]))','formatString':'#,0'})
    bar(b,'tenure','FactSubscription','tenure_bucket','Tenure Cancellations',(905,705,650,250),'Cancellations by tenure · counts, not hazard')
    d=page('Billing','Billing Health & Revenue at Risk');slicers(d)
    cards(d,['Failed Payment Rate','Failed Payments','Open Invoice Value','Accounts With Failed Payments','MRR at Risk'])
    line(d,'outcomes',['Succeeded Payments','Failed Payments'],(35,255,800,310),'Payment outcomes by attempt month')
    bar(d,'failedseg','DimAccount','segment','Failed Payment Rate',(855,255,330,310),'Failure rate by segment')
    bar(d,'openplan','DimPlan','plan_name','Open Invoice Value',(1205,255,350,310),'Open invoice value · final status')
    # Landmark selector makes the fixed prediction window explicit; main date selector does not act here.
    visual(d,'landmarkselector','slicer',{'Values':[('FactLandmark','landmark',False)]},(35,590,440,80),'Landmark date · independent of billing date slicer')
    bar(d,'billingchurn','FactLandmark','risk_group','Landmark Churn 90d',(35,695,440,260),'Next 90-day churn · selected landmark(s)')
    visual(d,'riskqueue','tableEx',{'Values':[('DimAccount','account_id',False),('DimAccount','segment',False),('DimPlan','plan_name',False),('FactSubscription','Latest Priority MRR',True),('FactSubscription','Priority Failed Attempts',True),('FactSubscription','Priority Mature Balance',True)]},(495,590,1060,365),'Priority matrix · 31 Dec 2025 only; date slicer does not change this queue')
    write(definition/'pages'/'pages.json',{'$schema':SCHEMA+'item/report/definition/pagesMetadata/1.0.0/schema.json','pageOrder':pages,'activePageName':'Executive'})
    write(MODEL/'model.bim',model)
    (PBI/'measures.dax').write_text('\n\n'.join(n+' =\n'+e for n,(e,_) in MEASURES.items()))
    write(PBI/'theme.json',{'name':'SaaS Executive','dataColors':['#2874A6','#168A87','#C75A5A','#74869C'],'background':'#F2F5F8','foreground':'#13253C','tableAccent':'#2874A6','textClasses':{'title':{'fontFace':'Segoe UI','fontSize':13},'callout':{'fontFace':'Segoe UI','fontSize':25},'label':{'fontFace':'Segoe UI','fontSize':10}}})
    print(f'Generated {len(tables)} tables, {len(relations)} relationships and {len(pages)} PBIR pages. Desktop verification pending.')

if __name__=='__main__':build()
