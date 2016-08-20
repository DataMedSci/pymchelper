#!/usr/local/bin/rexx

say "Convert the card.db file to card.ini"

call import "flukalib.r"

fin = open("card.db","r")
fout = open("card.ini","w")

@WIDTH = 14
sdum = 0

groups_list = ""
assertcuont = 0

do forever
	line = read(fin)
	if eof(fin) then leave
	if line = "" then iterate
	if line=="-break-" then leave
	parse var line var value
	select
		when var=="name" then do
			call lineout fout
			call lineout fout,"["value"]"
			say value
			sdum = 0
			r    = -1
			assertcount = 0
		end

		when var == "range" then do
			e    = 0
			sdum = 0
			r = r + 1
			assertcount = 0
			value = swapsdum(value)
			call writeval fout, var"."r, value
		end

		when var == "defaults" then do
			value = swapsdum(value)
			call writeval fout, var"."r, value
		end

		when var == "extra" then do
			e = e + 1
			value = readblock(fin, value)
			if wordpos("nix",value) = 0 then do
				if ^sdum & e = 7 then do
					call writeval fout, var"."r".0", value
					sdum = 1
					e = e - 1
				end; else
					call writeval fout, var"."r"."e, value
			end; else do
				parse var value . nix
				if ^sdum & e = 7 then do
					sdum = 1
					e = e - 1
				end
				if datatype(nix,"N") then e = e + nix - 1
			end
		end

		when var == "meaning" then do
			value = readblock(fin, value)
			call writeval fout, var, value
		end

		when var == "assert" then do
			call writeval fout, var"."r"."||assertcount, value
			assertcount = assertcount + 1
		end

		when left(var,1)='#' then
			call lineout fout, line

		otherwise
			/* all other variables */
			call writeval fout, var, value
	end
end

/* Particles */
call lineout fout
call lineout fout,'[particles]'
do forever
	line = read(fin)
	if eof(fin) then leave
	if line = "" then iterate
	if line=="-break-" then leave
	if left(line,1) == "#" then do
		call lineout fout,';'substr(line,2)
		iterate
	end
	parse var line name id mass comment
	last = word(comment,words(comment))
	if datatype(last,'N') | last="---" then do
		pdg = last
		comment = subword(comment, 1, words(comment)-1)
	end; else
		pdg = "---"
	call writeval fout, "pid."id, name
	call writeval fout, "mass."id, mass
	call writeval fout, "comment."id, strip(comment)
	call writeval fout, "pdg."id, pdg
end

/* Materials */
call lineout fout
call lineout fout,'[materials]'
do forever
	line = read(fin)
	if eof(fin) then leave
	if line = "" then iterate
	if line=="-break-" then leave
	if left(line,1) == "#" then do
		call lineout fout,';'substr(line,2)
		iterate
	end

	parse var line name id desc +30 Amass Z rho
	call writeval fout, "mat."id, name
	call writeval fout, "desc."id, strip(desc)
	call writeval fout, "Amass."id, Amass
	call writeval fout, "Z."id, Z
	call writeval fout, "rho."id, rho
	call lineout fout
end

/* Groups */
call lineout fout
call lineout fout,'[n-groups]'
m = 0

len    = 6
units  = "MeV keV eV"
nunits = words(units)
groups = 0
do forever
	line = read(fin)
	if eof(fin) then leave
	if line = "" then iterate
	if line=="-break-" then leave
	if left(line,1) == "#" then do
		call lineout fout,';'substr(line,2)
		iterate
	end
	parse var line id energy
	if id=="groups" then do
		groups = energy
		if wordpos(groups,groups_list)=0 then groups_list = groups_list groups
		iterate
	end

	/*parse var line =24 id +4 . . energy .*/
	id = strip(id)
	if id>m then m=id
	if id="" then id=m+1

	ene = energy
	log = abs(trunc(log10(ene)))%3 + 1
	if log <= nunits then
		e = ene * 1000**log
	else do
		log = nunits
		e = ene * 1000**nunits
	end

	n = translate(FlukaFormat(e,len),"E","D")
	if length(n)<len then
		if pos("E",n) = 0 then n=left(n,len,"0")
	u = word(units,log)

	call writeval fout, "ene."groups"."id,energy n u
end
call writeval fout, 'groups', groups_list

/* LOW-NEUT Materials */
call lineout fout
call lineout fout,'[low-neut]'
id = 0
groups = 0
do forever
	line = read(fin)
	if eof(fin) then leave
	if line = "" then iterate
	if line=="-break-" then leave
	if left(line,1) == "#" then do
		call lineout fout,';'substr(line,2)
		iterate
	end
	if word(line,1) == "groups" then do
		groups = word(line,2)
		id = 0
		if wordpos(groups,groups_list)=0 then groups_list = groups_list groups
		iterate
	end

	parse var line elem material +29 temp db rn name id1 id2 id3 g
	if name=="available" then iterate

	id = id + 1
	call writeval fout, "elem."groups"."id, elem
	call writeval fout, "mat."groups"."id, strip(material)
	call writeval fout, "temp."groups"."id, temp
	call writeval fout, "db."groups"."id, db
	call writeval fout, "rn."groups"."id, rn
	call writeval fout, "name."groups"."id, name
	call writeval fout, "ids."groups"."id, id1 id2 id3
	call writeval fout, "g."groups"."id, g
	call lineout fout
end

/* User routines */
call lineout fout
call lineout fout,'[usermvax]'
m = 0

do forever
	line = read(fin)
	if eof(fin) then leave
	if line = "" then iterate
	if line=="-break-" then leave
	if left(line,1) == "#" then do
		call lineout fout,';'substr(line,2)
		iterate
	end
	parse var line routine desc
	lower routine
	call writeval fout, routine, desc
end

call close fin
call close fout
return

writeval: procedure expose @WIDTH
	parse arg fout, var, value
	call lineout fout, left(var"=",@WIDTH)||value
return

/* --- readblock --- */
readblock: procedure expose @WIDTH
	parse arg fin, value
	value = strip(value)
	do forever
		if right(value,1)==";" then
			return left(value,length(value)-1)
		value = value||"0A"x||copies(" ",@WIDTH)||strip(read(fin))
	end

/* --- swapsdum --- */
swapsdum: procedure
	parse arg w1 w2 w3 w4 w5 w6 sdum rest
	return strip(sdum w1 w2 w3 w4 w5 w6 rest)
