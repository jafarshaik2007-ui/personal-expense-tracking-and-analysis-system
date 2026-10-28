(function(){
  const palette=['#6ee7b7','#a78bfa','#fbbf80','#7dd3fc','#fda4af','#c4b5fd'];
  function render(data){
    if(!window.Chart) return;
    const cash=document.getElementById('cashFlowChart');
    if(cash) new Chart(cash,{type:'bar',data:{labels:data.labels,datasets:[{label:'Income',data:data.income,backgroundColor:'#75dfb5',borderRadius:5,maxBarThickness:20},{label:'Expenses',data:data.expenses,backgroundColor:'#b7a0f8',borderRadius:5,maxBarThickness:20}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{usePointStyle:true,boxWidth:7,color:'#8d96a7',font:{family:'DM Sans',size:11},padding:18}},tooltip:{callbacks:{label:c=>`${c.dataset.label}: ₹${Number(c.raw).toLocaleString('en-IN')}`}}},scales:{x:{grid:{display:false},ticks:{color:'#8d96a7',font:{family:'DM Sans',size:10}},border:{display:false}},y:{beginAtZero:true,grid:{color:'rgba(140,150,170,.13)'},ticks:{color:'#8d96a7',callback:v=>'₹'+Number(v).toLocaleString('en-IN'),font:{size:10}},border:{display:false}}}}});
    const pie=document.getElementById('categoryChart');
    if(pie) new Chart(pie,{type:'doughnut',data:{labels:data.categories,datasets:[{data:data.amounts,backgroundColor:palette,borderWidth:0,hoverOffset:5}]},options:{responsive:true,maintainAspectRatio:false,cutout:'72%',plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${c.label}: ₹${Number(c.raw).toLocaleString('en-IN')}`}}}}});
  }
  window.PennywiseCharts={render};
})();