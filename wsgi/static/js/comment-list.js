commentList = {
	bind: function(listBox, pid, authenticated){
		commentList.listBox = listBox;
		commentList.pid = pid;
		commentList.authenticated = authenticated;
		commentList.refresh();
	},

	genFoldButton: function(){
		return $("<button class=\"btn btn-default btn-xs fold-toggler\">Unfold &darr;</button>").click(commentList.toggleFold);
	},

	genWriteButton: function(){
		return $("<button class=\"btn btn-primary btn-xs write-opener\" disabled>Write</button>").click(commentList.openWrite);
	},

	refresh: function(){
		commentList.listBox.attr({class: "panel panel-default post-list-container", cid: "-1", opened: "false", writing: "false"}).append("<div class=\"panel-heading\"><span class=\"glyphicon glyphicon-comment\" aria-hidden=\"true\"></span> Comments</div>").append(commentList.genFoldButton()).append(commentList.genWriteButton());
	},
	
	deletePost: function(event){
		if(confirm("Are you sure you want to delete this comment?\nAll of its offsprings would also be deleted, and unable to be recovered.")){
			var cid = parseInt($(event.target).parent().parent().children(".post-list-container").attr("cid"));
			$.post("/i/comment/",
					{operation: "del",
						cid: cid.toString()},
						function(info){
							if(info == "Success")
								commentList.destroy($(event.target).parent().parent());
							else
								alert("Failure in deleting the comment.");
						}
					);
		}
	},

	addDeleteButton: function(comp){
		if(commentList.authenticated)
			comp.append(' ').append($('<button class=\"btn btn-danger btn-xs\">Delete</button>').click(commentList.deletePost));
		return comp;		
	},

	addPost: function(list, val){
		list.append($("<li class=\"list-group-item\"></li>").append(commentList.addDeleteButton($("<h4><a href=\"mailto:" + val.poster_email + "\">" + val.poster_name + "</a></h4>"))).append("<div class=\"container\">" + val.contents + "</div>").append("<small>Posted @ " + val.time + "</small>").append("<hr/>").append($("<div class=\"panel panel-default post-list-container\"></div>")
					.attr({cid: val.id.toString(), opened: "false", writing: "false"}).append(commentList.genFoldButton()).append(commentList.genWriteButton())));
	},	

	destroy: function(t){
		t.slideUp(1000, 
				function(){
					t.remove();
				});
	},

	toggleFold: function(event){
		var c = $(event.target).parent();
		if(c.attr("opened") == "false"){
			var cid = parseInt(c.attr("cid"));
/*						var li = $("<ul class=\"list-group\" hidden=\"hidden\"></ul>");
						commentList.addPost(li, {id: 0});
						commentList.addPost(li, {id: 0});
						c.children(".fold-toggler").before(li);
						li.slideDown(1000);*/
			$.getJSON("/i/comment/", { pid: commentList.pid.toString(), cid: cid.toString() }, 
					function(posts){
						var li = $("<ul class=\"list-group\" hidden=\"hidden\"></ul>");
						$.each(posts,
								function(i, val){
									commentList.addPost(li, val);
								}
							  );
						c.children(".fold-toggler").before(li);
						li.slideDown(1000);
						c.attr("opened", "true");
						c.children(".write-opener").attr("disabled", false);
						c.children(".fold-toggler").html("Fold &uarr;");
					}
					);
		} else{
			if(c.attr("writing") == "true"){
				commentList.destroy(c.children(".post-write"));
				c.attr("writing", "false");
			}
			commentList.destroy(c.children("ul"));
			c.children(".write-opener").attr("disabled", true);
			c.attr("opened", "false");
			c.children(".fold-toggler").html("Unfold &darr;");
		}
	},
	openWrite: function(event){
		var c = $(event.target).parent();
		if(c.attr("opened") == "false")
			return;
//			commentList.toggleFold(event);
		if(c.attr("writing") == "false"){
			c.attr("writing", "true");
			var wbox = $("<div class=\"post-write container-fluid \" hidden=\"hidden\"></div>")
				.append("<textarea class=\"form-control col-sm-12 contents\" rows=\"5\"></textarea>")
				.append("<input class=\"form-control poster-name\" type=\"text\" placeholder=\"Your name\"/>")
				.append("<input class=\"form-control poster-email\" type=\"text\" placeholder=\"Your email\"/>")
				.append($("<button class=\"btn btn-primary\">Post</button>").click(commentList.postComment))
				.append($("<button class=\"btn btn-default\">Cancel</button>").click(commentList.closeWrite))
				.append("<span class=\"infobox\" hidden=\"hidden\"></span>");
			c.children("ul").after(wbox);
			wbox.slideDown(1000);
		}
	},
	closeWrite: function(event){
		var c = $(event.target).parent().parent();
		if(c.attr("opened") == "true" && c.attr("writing") == "true"){
			c.attr("writing", "false");
			commentList.destroy($(event.target).parent());
		}
	},
	postComment: function(event){
		var c = $(event.target).parent();
		var post = {
			poster_name: c.children(".poster-name").val(),
			poster_email: c.children(".poster-email").val(),
			contents: c.children(".contents").val()
		};
		if(!post.poster_name || !post.poster_email || !post.contents){
			var infobox = c.children(".infobox").html("Invalid input!");
			c.append(infobox);
			infobox.fadeIn(1000, function(){
				setTimeout(function(){
					infobox.fadeOut(5000);
				}, 5000);
			});
			return;
		}
		var cid = parseInt(c.parent().attr("cid"));
		var li = c.parent().children("ul");
		c.parent().attr("writing", "false");
		commentList.destroy(c);
		$.post("/i/comment/", {pid: commentList.pid.toString(), cid: cid.toString(), post: JSON.stringify(post)}, function(rpost){
			commentList.addPost(li, rpost);
		}, "json");
	}
};

