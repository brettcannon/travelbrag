run:
    py -m travelbrag

# Deploy to production
publish:
    netlify deploy --prod --dir=site
