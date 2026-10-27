export const categoryLabel = (category: string) => category === '__unknown__' ? 'Unknown ancestry' : `Lineage ${category}`;

const colors = ['#216d62','#8ca959','#bc8a50','#706c98','#769da9','#a67882'];

export function CompositionBar({categories,label}: {categories: [string,number][];label:string}) {
  return <div className="composition-bar" role="img" aria-label={label}>
    {categories.map(([category,proportion],index) => <span key={category} style={{width:`${proportion*100}%`,background:colors[index%colors.length]}} title={`${categoryLabel(category)}: ${(proportion*100).toFixed(1)}%`}>{proportion>=.1 ? categoryLabel(category) : ''}</span>)}
  </div>;
}
