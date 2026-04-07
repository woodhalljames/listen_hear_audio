Currently in the middle of a transition to dark theme for site, while also consolidating the styling for every page (excluding django admin) and use the project.css to get the styling for every page. many buttons do not work with the colors and need to utilize the outline (that is now better in the project.css)

account dashboard, careers, blog, builder scheduler all need to accomodate these new stylings / use projects static when possible. 

also lets update the footer bg color /styling to be more in line with the final colors 


root {
  /* Official Brand Colors (Always stay the same) */
  --brand-blue: #0341FC;
  --brand-yellow: #FFFF00;

  /* UI Colors (These change based on mode) */
  --ui-primary: var(--brand-blue);
  --ui-accent: var(--brand-yellow);
  --bg-color: #FFFFFF;
  --text-color: #1A1A1A;
}

@media (prefers-color-scheme: dark) {
  :root {
    /* UI variants for better readability */
    --ui-primary: #858CF8;   /* Softer Blue */
    --ui-accent: #FEFE4C;    /* Golden Yellow */
    
    --bg-color: #121212;
    --text-color: #F5F5F5;
  }
}

/* Usage */
.navbar { 
  background-color: var(--brand-blue); 
  border-bottom: 3px solid var(--brand-yellow); 
}

.button-primary { 
  background-color: var(--ui-primary); 
}

.link-accent { 
  color: var(--ui-accent); 
}
