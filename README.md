# BHV: Behavioral Health Vault

The goal of this project is to provide a digitization approach to record the journey of recovery of people with serious mental illnesses and other social determinants. BHV (pronounced Beehive or Behave) aims to complement traditional Electronic Health Records (EHRs) by storing patient-provided images (photographs and scanned drawings) along with associated textual narratives, which may be provided by the patient or recorded by a social worker during an interview.

BHV is a minimal, Python-based application that enables healthcare networks to store and retrieve patient-provided images.

It provides them access to upload, view, and edit their own images and narratives.

It also provides admin-level access for system administrators to view the entire ecosystem, upload images on behalf of users, along with the narrative, edit images on behalf of users, and delete images or narrations on behalf of users or as a moderation action.

The system should be secure. But the signup process should be pretty straightforward. Email-based signups are ok. 

Log-ins should be straightforward. A simple username and password should be sufficient.

The system should avoid unnecessary bloat to enable easy installation in healthcare networks.

The front-end should be kept minimal to allow the entire system to be run from a single command (rather than expecting the front-end, backend, and database to be run separately).

The storage of the images could be in a file system with an index to retrieve them easily. The index itself could be in a database to allow easy queries.&#10;&#10;## Deployment to Vercel&#10;&#10;1. Push changes to GitHub: `git add . &amp;&amp; git commit -m "Add Vercel deployment config" &amp;&amp; git push`&#10;2. Go to [vercel.com](https://vercel.com), login, "New Project" → Import your GitHub repo.&#10;3. In Project Settings → Environment Variables, add:&#10;   - `SECRET_KEY`: Your app secret (generate with `openssl rand -hex 32`)&#10;   - `GOOGLE_CLIENT_ID`: From Google Console&#10;   - `GOOGLE_CLIENT_SECRET`: From Google Console&#10;   - `GOOGLE_REDIRECT_URI`: `https://your-project.vercel.app/auth/google/callback`&#10;4. Deploy! App live at your-project.vercel.app&#10;&#10;**Notes:**&#10;- SQLite data/uploads/sessions ephemeral (lost on redeploy). Migrate to Vercel Postgres for persistence.&#10;- Update Google OAuth authorized domains/redirects in console.&#10;- Test health: /health
