"""Static evidence previews, deliberately labeled separately from native Power BI acceptance."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter,PercentFormatter
from matplotlib.patches import FancyBboxPatch
import pandas as pd
import numpy as np
from data_processing import ROOT,OUT
INK='#13253C';BLUE='#2874A6';TEAL='#168A87';RED='#C75A5A';BG='#F2F5F8'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':'#D9E1E8','axes.labelcolor':INK,'text.color':INK,'xtick.color':'#657488','ytick.color':'#657488','axes.titleweight':'bold','axes.titlesize':12,'figure.facecolor':BG,'axes.facecolor':'white'})
money=FuncFormatter(lambda x,p:f'{x/1e6:.1f}m' if abs(x)>=1e6 else f'{x/1e3:.0f}k')

def base(title,sub,kpis):
    fig=plt.figure(figsize=(16,9),dpi=120)
    fig.text(.045,.948,title,fontsize=24,weight='bold')
    fig.text(.045,.914,sub,fontsize=10,color='#657488')
    n=len(kpis);width=.91/n
    for j,(label,value) in enumerate(kpis):
        x=.045+j*width
        card=FancyBboxPatch((x,.794),width-.012,.094,boxstyle='round,pad=0.008,rounding_size=.008',fc='white',ec='none',transform=fig.transFigure,zorder=-1)
        fig.add_artist(card);fig.text(x+.009,.854,label,fontsize=9,color='#657488');fig.text(x+.009,.812,value,fontsize=20,weight='bold')
    fig.text(.045,.022,'SYNTHETIC DATA • VERSION 1.0.0  |  Python analytical preview • native Power BI verification pending',fontsize=8,color='#657488')
    return fig

def chart(fig,pos,title):
    ax=fig.add_axes(pos);ax.set_title(title,loc='left',pad=15);ax.grid(axis='y',alpha=.14,zorder=0);return ax

def save(fig,name):
    fig.savefig(ROOT/'assets'/name,dpi=120,facecolor=BG);plt.close(fig)

def render(c,m,co,sv,lc,data,s):
    x=pd.to_datetime(m.month_start)
    fig=base('Executive SaaS Overview','Monthly subscription health  |  Jan 2023 – Dec 2025  |  Monetary units: CU',[
        ('Active customers',f"{s['active_customers']:,}"),('MRR',f"{s['mrr']/1e6:.3f}m"),('ARR run rate',f"{s['arr']/1e6:.2f}m"),('Logo churn · Dec',f"{s['dec_logo_churn']:.2%}"),('Gross retention · Dec',f"{1-s['dec_gross_revenue_churn']:.2%}")])
    ax=chart(fig,[.065,.435,.535,.28],'Recurring revenue trajectory');ax.plot(x,m.active_mrr,color=BLUE,lw=2.8);ax.fill_between(x,m.active_mrr,alpha=.08,color=BLUE);ax.yaxis.set_major_formatter(money)
    ax=chart(fig,[.67,.435,.28,.28],'Active MRR by plan');d=pd.Series(s['plan_active_mrr']).sort_values();ax.barh(d.index,d,color=[BLUE]*len(d));ax.xaxis.set_major_formatter(money);ax.grid(False)
    ax=chart(fig,[.065,.11,.245,.23],'Customer movement');ax.bar(x,m.new_customers,width=18,color=TEAL,label='New');ax.bar(x,-m.churned_customers,width=18,color=RED,label='Cancelled');ax.legend(frameon=False,fontsize=8)
    ax=chart(fig,[.385,.11,.245,.23],'Logo churn by month');ax.plot(x,m.logo_churn_rate,color=RED,lw=2);ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax=chart(fig,[.705,.11,.245,.23],'Cancellation MRR');ax.bar(x,m.churned_mrr,width=20,color=BLUE);ax.yaxis.set_major_formatter(money)
    for a in fig.axes:a.tick_params(axis='x',labelsize=8)
    save(fig,'executive_dashboard.png')
    fig=base('Customer Retention Intelligence','Cohorts use month-end survival  |  Newer unobservable ages remain blank',[
        ('Cancellations · all history',f"{s['cancelled']:,}"),('Retention · December',f"{1-s['dec_logo_churn']:.2%}"),('Mean tenure at churn',f"{s['avg_churn_tenure_days']:.0f} days"),('Cancelled MRR · all history',f"{s['churned_mrr_all']/1e3:.0f}k")])
    mat=co.pivot(index='cohort',columns='age_months',values='retention').iloc[:, :25];mat.index=pd.to_datetime(mat.index).strftime('%b %y')
    ax=chart(fig,[.065,.115,.49,.59],'Customer retention by acquisition cohort');ax.grid(False);im=ax.imshow(mat.values,aspect='auto',vmin=.65,vmax=1,cmap='YlGnBu');ax.set_yticks(range(0,len(mat),3),mat.index[::3],fontsize=8);ax.set_xticks(range(0,25,3));ax.set_xlabel('Months since start');fig.colorbar(im,ax=ax,fraction=.035,pad=.025,format=PercentFormatter(1))
    expo=pd.read_csv(OUT/'subscription_monthly_snapshot.csv').merge(c[['account_id','plan_name','segment','region','acquisition_channel']],on='account_id')
    for dim,pos,title in [('plan_name',[.66,.445,.285,.26],'Pooled monthly churn by plan'),('acquisition_channel',[.66,.11,.285,.24],'Pooled monthly churn by channel')]:
        d=expo.groupby(dim)[['churned_customers','beginning_customers']].sum();d=(d.churned_customers/d.beginning_customers).sort_values();ax=chart(fig,pos,title);ax.barh(d.index,d,color=BLUE);ax.xaxis.set_major_formatter(PercentFormatter(1));ax.grid(False)
    save(fig,'retention_dashboard.png')
    fig=base('Billing Health & Revenue at Risk','Priority: failures/retries in 30 days or reconstructed balance ≥30 days overdue',[
        ('Attempt failure rate · all',f"{s['failed_payment_rate']:.2%}"),('Open invoice value · all',f"{s['open_invoice_value']/1e6:.2f}m"),('Priority accounts',f"{s['risk_accounts']:,}"),('Priority MRR · Dec',f"{s['risk_mrr']/1e3:.0f}k")])
    p=data['payments'].copy();p['month']=p.attempted_at.dt.to_period('M').dt.to_timestamp();pv=p.groupby(['month','payment_status']).size().unstack(fill_value=0)
    ax=chart(fig,[.065,.445,.49,.26],'Payment attempts over time');ax.plot(pv.index,pv.succeeded,color=BLUE,label='Succeeded');ax.plot(pv.index,pv.failed,color=RED,label='Failed');ax.legend(frameon=False,fontsize=9)
    latest=lc[lc.landmark==pd.Timestamp('2025-09-30')];ax=chart(fig,[.67,.445,.28,.26],'Next 90-day churn · Sep landmark');ax.bar(latest.risk_group,latest.churn_90d,color=TEAL);ax.yaxis.set_major_formatter(PercentFormatter(1));ax.tick_params(axis='x',labelsize=8)
    risk=pd.read_csv(OUT/'billing_risk_accounts.csv');ax=chart(fig,[.065,.11,.49,.23],'Priority MRR by segment');d=risk[risk.risk_flag==1].groupby('segment').mrr.sum().sort_values();ax.barh(d.index,d,color=BLUE);ax.xaxis.set_major_formatter(money);ax.grid(False)
    ax=fig.add_axes([.67,.11,.28,.23]);ax.axis('off');ax.text(0,1,'Interpretation guardrail',fontsize=12,weight='bold',va='top');ax.text(0,.76,'All non-void December invoices are open.\nNo December invoice collections are recorded.\nTreat terminal-month collections as provisional.\n\nBilling groups are observational;\nthese signals do not prove causation.',fontsize=11,linespacing=1.6,va='top')
    save(fig,'billing_dashboard.png')
    fig,ax=plt.subplots(figsize=(13,9));im=ax.imshow(mat.values,aspect='auto',vmin=0,vmax=1,cmap='YlGnBu');ax.set_yticks(range(len(mat)),mat.index,fontsize=8);ax.set_xticks(range(25));ax.set_xlabel('Months since subscription start');ax.set_title('Month-end cohort retention • blank = unobservable',loc='left');fig.colorbar(im,ax=ax,format=PercentFormatter(1));fig.tight_layout();save(fig,'cohort_heatmap.png')
    fig,axes=plt.subplots(1,3,figsize=(16,5))
    for ax,dim in zip(axes,['plan_name','segment','acquisition_channel']):
        for group,g in sv[sv.dimension==dim].groupby('group'):
            ax.step(g.day,g.survival,where='post',label=group,lw=1.8);ax.fill_between(g.day,g.lower95,g.upper95,step='post',alpha=.07)
        ax.set_title(dim.replace('_',' ').title(),loc='left');ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_xlabel('Days since subscription start');ax.set_ylim(.5,1.02);ax.legend(frameon=False,fontsize=8)
    fig.suptitle('Kaplan–Meier subscription persistence • 95% Greenwood intervals',x=.05,ha='left',weight='bold');fig.tight_layout();save(fig,'survival_curves.png')
    fig,ax=plt.subplots(figsize=(14,7));ax.axis('off')
    nodes={'DimAccount':(.03,.7),'DimPlan':(.03,.24),'MonthlySnapshot':(.36,.83),'FactSubscription':(.36,.63),'FactInvoice':(.36,.43),'FactPayment':(.36,.23),'FactCohort':(.36,.03),'DimDate':(.77,.45)}
    for name,(xx,yy) in nodes.items():
        ax.add_patch(FancyBboxPatch((xx,yy),.2,.12,boxstyle='round,pad=.015',fc='white',ec=BLUE));ax.text(xx+.1,yy+.065,name,ha='center',va='center',weight='bold')
    for source in ['DimAccount','DimPlan']:
        for target in ['MonthlySnapshot','FactSubscription','FactInvoice','FactPayment','FactCohort']:
            xx,yy=nodes[source];tx,ty=nodes[target];ax.annotate('',xy=(tx,ty+.06),xytext=(xx+.2,yy+.06),arrowprops={'arrowstyle':'->','color':'#AAB9C8','lw':.8})
    for target in ['MonthlySnapshot','FactInvoice','FactPayment']:
        xx,yy=nodes['DimDate'];tx,ty=nodes[target];ax.annotate('',xy=(tx+.2,ty+.06),xytext=(xx,yy+.06),arrowprops={'arrowstyle':'->','color':TEAL,'lw':1.2})
    ax.set_title('Conformed analytical model • single-direction 1:* filters',loc='left',pad=20);ax.set_xlim(0,1);ax.set_ylim(-.08,1);fig.tight_layout();save(fig,'data_model.png')
